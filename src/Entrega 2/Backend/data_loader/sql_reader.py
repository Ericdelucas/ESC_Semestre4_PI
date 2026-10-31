"""Leituras SQL da tabela cti_dados — filtros e agregacoes no PostgreSQL."""

from __future__ import annotations

import time

import pandas as pd
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, OperationalError

from Backend.data_loader.csv_reader import otimizar_base_cti
from Backend.data_loader.db import dispose_engine, get_cti_engine, postgres_disponivel
from Backend.diag import diag

TABLE = "cti_dados"
_COUNT_CACHE: int | None = None
_CONTAS_CACHE: list[str] | None = None


def fonte_label() -> str:
    return "cti_dados (PostgreSQL)"


def _normalizar_colunas(frame: pd.DataFrame) -> pd.DataFrame:
    if frame is None or frame.empty:
        return frame
    rename: dict[str, str] = {}
    for col in frame.columns:
        chave = str(col)
        if chave.upper() in {"ANO", "CENA", "CONTA", "VALOR"}:
            rename[col] = chave.upper()
        elif chave.lower() == "ano_num":
            rename[col] = "ano_num"
    return frame.rename(columns=rename) if rename else frame


def _executar(sql: str, params: dict | None = None, tentativas: int = 3) -> pd.DataFrame:
    ultimo: Exception | None = None
    for tentativa in range(1, tentativas + 1):
        try:
            diag("sql", f"a executar tentativa={tentativa}/{tentativas}")
            engine = get_cti_engine()
            with engine.connect() as conn:
                return _normalizar_colunas(pd.read_sql(text(sql), conn, params=params or {}))
        except (OperationalError, DBAPIError, RuntimeError) as exc:
            ultimo = exc
            diag(
                "sql",
                f"consulta falhou tentativa={tentativa}/{tentativas} {type(exc).__name__}: {exc}",
            )
            texto = str(exc).lower()
            dispose_engine()
            if any(
                k in texto
                for k in (
                    "translate host",
                    "name or service not known",
                    "resolvivel",
                    "network is unreachable",
                    "ipv4",
                )
            ):
                break
            time.sleep(0.45 * tentativa)
    assert ultimo is not None
    raise ultimo


def _escalar(sql: str, params: dict | None = None) -> object:
    ultimo: Exception | None = None
    for tentativa in range(1, 4):
        try:
            engine = get_cti_engine()
            with engine.connect() as conn:
                return conn.execute(text(sql), params or {}).scalar()
        except (OperationalError, DBAPIError, RuntimeError) as exc:
            ultimo = exc
            diag("sql", f"escalar falhou tentativa={tentativa} {type(exc).__name__}: {exc}")
            texto = str(exc).lower()
            dispose_engine()
            if any(
                k in texto
                for k in (
                    "translate host",
                    "name or service not known",
                    "resolvivel",
                    "network is unreachable",
                    "ipv4",
                )
            ):
                break
            time.sleep(0.45 * tentativa)
    assert ultimo is not None
    raise ultimo


def contar_linhas() -> int:
    global _COUNT_CACHE
    if _COUNT_CACHE is not None:
        return _COUNT_CACHE
    valor = _escalar(f"SELECT COUNT(*) FROM {TABLE}")
    _COUNT_CACHE = int(valor or 0)
    diag("sql", f"COUNT(*) cti_dados={_COUNT_CACHE:,}")
    return _COUNT_CACHE


def listar_anos() -> list[int]:
    frame = _executar(f'SELECT DISTINCT ano_num FROM {TABLE} WHERE ano_num IS NOT NULL ORDER BY 1')
    if frame.empty:
        return []
    return [int(v) for v in frame.iloc[:, 0].tolist() if pd.notna(v)]


def listar_cenas() -> list[str]:
    frame = _executar(f'SELECT DISTINCT "CENA" FROM {TABLE} WHERE "CENA" IS NOT NULL ORDER BY 1')
    if frame.empty:
        return []
    return [str(v) for v in frame.iloc[:, 0].tolist()]


def listar_contas() -> list[str]:
    global _CONTAS_CACHE
    if _CONTAS_CACHE is not None:
        return _CONTAS_CACHE
    frame = _executar(f'SELECT DISTINCT "CONTA" FROM {TABLE} WHERE "CONTA" IS NOT NULL')
    _CONTAS_CACHE = [str(v) for v in frame.iloc[:, 0].tolist()] if not frame.empty else []
    diag("sql", f"contas distintas={len(_CONTAS_CACHE)}")
    return _CONTAS_CACHE


def _ano_param(ano_sel: str | int | None) -> int | None:
    if ano_sel is None:
        return None
    texto = str(ano_sel).strip()
    if texto in {"Todos", "__all__", "All", "all", ""}:
        return None
    return int(float(texto))


def fetch_recorte(cena_sel: str | None, ano_sel: str | int | None) -> pd.DataFrame:
    """Fatia filtrada no banco. 'Todos' os cenarios devolve media por ANO/CONTA."""
    from Backend.metrics.financial_kpis import is_all_scenarios

    ano = _ano_param(ano_sel)
    if is_all_scenarios(cena_sel):
        sql = f"""
            SELECT "ANO",
                   MIN(ano_num) AS ano_num,
                   CAST('Todos' AS TEXT) AS "CENA",
                   "CONTA",
                   AVG("VALOR") AS "VALOR"
            FROM {TABLE}
            WHERE (:ano IS NULL OR ano_num = :ano)
            GROUP BY "ANO", "CONTA"
        """
        diag("sql", f"recorte agregado cena=Todos ano={ano}")
        frame = _executar(sql, {"ano": ano})
    else:
        sql = f"""
            SELECT "ANO", ano_num, "CENA", "CONTA", "VALOR"
            FROM {TABLE}
            WHERE "CENA" = :cena
              AND (:ano IS NULL OR ano_num = :ano)
        """
        diag("sql", f"recorte cena={cena_sel} ano={ano}")
        frame = _executar(sql, {"cena": str(cena_sel), "ano": ano})
    diag("sql", f"recorte linhas={len(frame):,} cols={list(frame.columns)}")
    return otimizar_base_cti(frame)


def fetch_wide_indicadores() -> pd.DataFrame:
    """Pivota contas canonicas no PostgreSQL: ~cenarios x anos, sem o CSV de 1M."""
    from Backend.metrics.column_resolver import resolve_account_name
    from Backend.metrics.financial_kpis import mapa_contas

    mapa = mapa_contas()
    oficiais = list(mapa.keys())
    campo_contas: dict[str, list[str]] = {}
    for conta in listar_contas():
        oficial = resolve_account_name(conta, oficiais)
        campo = mapa.get(oficial) or mapa.get(conta)
        if campo:
            campo_contas.setdefault(campo, []).append(conta)

    if not campo_contas:
        diag("sql", "nenhuma conta mapeada em cti_dados")
        return pd.DataFrame(columns=["ANO", "ano_num", "CENA"])

    selects = ['"ANO"', "ano_num", '"CENA"']
    params: dict[str, str] = {}
    for i, (campo, contas) in enumerate(sorted(campo_contas.items())):
        chaves: list[str] = []
        for j, conta in enumerate(contas):
            chave = f"c{i}_{j}"
            params[chave] = conta
            chaves.append(f":{chave}")
        selects.append(
            f'COALESCE(SUM("VALOR") FILTER (WHERE "CONTA" IN ({", ".join(chaves)})), 0) AS "{campo}"'
        )
    sql = f"""
        SELECT {", ".join(selects)}
        FROM {TABLE}
        GROUP BY "ANO", ano_num, "CENA"
    """
    diag("sql", f"wide SQL campos={len(campo_contas)} contas={sum(len(v) for v in campo_contas.values())}")
    frame = _executar(sql, params)
    diag("sql", f"wide linhas={len(frame):,} cols={list(frame.columns)}")
    return frame


def load_dashboard_from_sql() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    from Backend.metrics.financial_kpis import montar_indicadores_from_wide

    diag("sql", "a montar indicadores a partir de cti_dados")
    wide = fetch_wide_indicadores()
    diag("sql", f"wide shape={wide.shape}")
    ind, ranking = montar_indicadores_from_wide(wide)
    diag("sql", f"indicadores shape={ind.shape} ranking shape={ranking.shape}")
    df = fetch_recorte("Todos", "Todos")
    diag("sql", f"recorte shape={df.shape}")
    if df is None or df.empty:
        from Backend.services.dashboard_pipeline import df_longo_de_indicadores

        diag("sql", "recorte vazio — a reconstruir df a partir de indicadores")
        df = df_longo_de_indicadores(ind)
    diag("sql", f"dashboard SQL pronto df={len(df):,} ind={len(ind):,} ranking={len(ranking):,}")
    return df, ind, ranking


__all__ = [
    "contar_linhas",
    "fetch_recorte",
    "fetch_wide_indicadores",
    "fonte_label",
    "listar_anos",
    "listar_cenas",
    "listar_contas",
    "load_dashboard_from_sql",
    "postgres_disponivel",
]
