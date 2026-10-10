"""Leitura e normalizacao tolerante de uploads CSV/XLSX para o formato longo CTI."""

from __future__ import annotations

import logging
import re
import traceback
import unicodedata
from io import BytesIO, StringIO
from pathlib import Path

import pandas as pd

from Backend.data_loader.csv_reader import normalizar_conta, parse_valor_br
from Backend.metrics.column_resolver import resolve_account_name

logger = logging.getLogger("cti.upload")

REQUIRED_LONG_COLUMNS = ["ANO", "CENA", "CONTA", "VALOR", "ano_num"]
_VAZIOS = {"", "nan", "none", "nat", "<na>", "<nat>", "null", "n/a", "-"}

COLUMN_ALIASES: dict[str, str] = {
    "ano": "ANO",
    "year": "ANO",
    "periodo": "ANO",
    "period": "ANO",
    "exercicio": "ANO",
    "ano ref": "ANO",
    "ano referencia": "ANO",
    "ano num": "ano_num",
    "anonum": "ano_num",
    "ano numero": "ano_num",
    "n ano": "ano_num",
    "nr ano": "ano_num",
    "year num": "ano_num",
    "year number": "ano_num",
    "conta": "CONTA",
    "indicador": "CONTA",
    "metrica": "CONTA",
    "metric": "CONTA",
    "account": "CONTA",
    "rubrica": "CONTA",
    "descricao": "CONTA",
    "description": "CONTA",
    "nome conta": "CONTA",
    "valor": "VALOR",
    "value": "VALOR",
    "amount": "VALOR",
    "montante": "VALOR",
    "vlr": "VALOR",
    "vl": "VALOR",
    "importe": "VALOR",
    "cena": "CENA",
    "cenario": "CENA",
    "scenario": "CENA",
    "id cenario": "CENA",
    "idcenario": "CENA",
    "id scene": "CENA",
    "id scenario": "CENA",
    "codigo cenario": "CENA",
    "cod cenario": "CENA",
    "n cenario": "CENA",
    "num cenario": "CENA",
    "scenario id": "CENA",
    "scenario code": "CENA",
    "nome cenario": "CENA",
    "nome do cenario": "CENA",
    "cenario nome": "CENA",
    "scenario name": "CENA",
    "label cenario": "CENA",
}
_ROTULOS_CENA = {
    "nome cenario",
    "nome do cenario",
    "cenario nome",
    "scenario name",
    "label cenario",
}


def _log(nivel: str, mensagem: str) -> None:
    print(f"[CTI upload] {mensagem}", flush=True)
    getattr(logger, nivel, logger.info)(mensagem)


def _slug(texto: object) -> str:
    bruto = str(texto or "").strip().lower()
    nfkd = unicodedata.normalize("NFKD", bruto)
    sem_acento = "".join(ch for ch in nfkd if not unicodedata.combining(ch))
    sem_acento = re.sub(r"\(.*?\)", " ", sem_acento)
    limpo = re.sub(r"[^a-z0-9]+", " ", sem_acento)
    return " ".join(limpo.split())


def _destino_coluna(nome: object) -> str | None:
    slug = _slug(nome)
    if not slug:
        return None
    if slug in COLUMN_ALIASES:
        return COLUMN_ALIASES[slug]
    for alias, destino in COLUMN_ALIASES.items():
        if slug.startswith(f"{alias} ") or slug.endswith(f" {alias}"):
            if alias in {"ano", "year"} and re.search(r"\d", slug):
                continue
            return destino
    return None


def _eh_vazio(valor: object) -> bool:
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return True
    return str(valor).strip().lower() in _VAZIOS


def _to_number(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce")
    texto = series.astype(str).str.replace("R$", "", regex=False).str.replace("%", "", regex=False).str.strip()
    return parse_valor_br(texto)


def mapear_colunas(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str]]:
    rename: dict[str, str] = {}
    usados: set[str] = set()
    for col in df.columns:
        destino = _destino_coluna(col)
        if destino and destino not in usados:
            rename[col] = destino
            usados.add(destino)
        else:
            rename[col] = str(col).strip()
    return df.rename(columns=rename), {str(origem): destino for origem, destino in rename.items()}


def _contar_mapeados(colunas: list[object]) -> int:
    destinos = {_destino_coluna(col) for col in colunas}
    destinos.discard(None)
    return len(destinos)


def _parece_cti_nativo(df: pd.DataFrame) -> bool:
    if df.empty or df.shape[1] < 3:
        return False
    primeiro = str(df.iloc[0, 0]).strip()
    return bool(re.match(r"(?i)^ano\s+\d+", primeiro))


def _limpar_grade(df: pd.DataFrame) -> pd.DataFrame:
    out = df.dropna(axis=0, how="all").dropna(axis=1, how="all")
    limpos: list[str] = []
    for idx, col in enumerate(out.columns):
        texto = "" if col is None else str(col).strip()
        if texto.lower() in {"", "none", "nan", "unnamed"}:
            texto = f"Unnamed_{idx}"
        limpos.append(texto)
    out.columns = limpos
    extras = [col for col in out.columns if col.lower().startswith("unnamed") and out[col].map(_eh_vazio).all()]
    if extras:
        out = out.drop(columns=extras)
    return out


def _promover_cabecalho(df: pd.DataFrame) -> pd.DataFrame:
    """Se a primeira linha for titulo, promove a linha com mais aliases a cabecalho."""
    if df.empty or _contar_mapeados(list(df.columns)) > 0:
        return df
    melhor_idx = None
    melhor_score = 0
    limite = min(4, len(df))
    for idx in range(limite):
        score = _contar_mapeados(list(df.iloc[idx].tolist()))
        if score > melhor_score:
            melhor_score = score
            melhor_idx = idx
    if melhor_idx is None or melhor_score == 0:
        return df
    promovido = df.iloc[melhor_idx + 1 :].copy()
    promovido.columns = [str(col).strip() for col in df.iloc[melhor_idx].tolist()]
    _log("info", f"Cabecalho promovido da linha {melhor_idx} (score={melhor_score}): {list(promovido.columns)}")
    return _limpar_grade(promovido)


def ler_upload(nome_arquivo: str, payload: bytes) -> tuple[pd.DataFrame, list[str]]:
    """Le CSV/Excel e devolve o DataFrame cru mais avisos de leitura."""
    avisos: list[str] = []
    suffix = Path(nome_arquivo).suffix.lower()
    _log("info", f"Arquivo recebido: '{nome_arquivo}' ({len(payload)} bytes, extensao={suffix or 'sem extensao'})")
    if suffix in {".xlsx", ".xls"}:
        bruto = _promover_cabecalho(_limpar_grade(pd.read_excel(BytesIO(payload), dtype=object)))
        _log("info", f"Excel lido com {len(bruto)} linha(s) e colunas originais {bruto.columns.tolist()}")
        return bruto, avisos

    texto = None
    encoding_usado = None
    for encoding in ("utf-8-sig", "utf-8", "latin-1", "cp1252"):
        try:
            texto = payload.decode(encoding)
            encoding_usado = encoding
            break
        except UnicodeDecodeError:
            continue
    if texto is None:
        raise ValueError(f"Nao foi possivel decodificar '{nome_arquivo}' (utf-8/latin-1/cp1252).")
    _log("info", f"CSV decodificado com encoding={encoding_usado}")

    dados = _promover_cabecalho(_limpar_grade(pd.read_csv(StringIO(texto), sep=None, engine="python")))
    mapeados = _contar_mapeados(list(dados.columns))
    _log("info", f"CSV com cabecalho: colunas={dados.columns.tolist()} mapeamentos_estruturais={mapeados}")
    if mapeados > 0:
        return dados, avisos

    nativo = pd.read_csv(StringIO(texto), header=None, names=["ANO", "CENA", "CONTA", "VALOR"])
    nativo = _limpar_grade(nativo)
    if _parece_cti_nativo(nativo):
        aviso = (
            f"Cabecalho de '{nome_arquivo}' nao reconheceu aliases estruturais "
            f"{list(dados.columns)}; arquivo lido no formato nativo CTI (ANO, CENA, CONTA, VALOR)."
        )
        avisos.append(aviso)
        _log("info", aviso)
        return nativo, avisos

    _log(
        "warning",
        f"Nenhum alias estrutural em {dados.columns.tolist()}. "
        "Mantendo cabecalhos originais para o diagnostico da normalizacao.",
    )
    return dados, avisos


def _unicos(valores: object) -> list:
    """Valores unicos sem passar lista crua a pd.unique (pandas 2.2+ recusa list)."""
    if valores is None:
        return []
    if isinstance(valores, pd.Index):
        return [item for item in valores.unique().tolist()]
    if isinstance(valores, pd.Series):
        return [item for item in valores.dropna().unique().tolist()]
    return [item for item in pd.Series(list(valores)).dropna().unique().tolist()]


def _consolidar_duplicadas(df: pd.DataFrame) -> pd.DataFrame:
    if df.columns.is_unique:
        return df
    partes: list[pd.DataFrame] = []
    for nome in _unicos(df.columns):
        bloco = df.loc[:, df.columns == nome]
        if bloco.shape[1] == 1:
            partes.append(bloco)
            continue
        soma = bloco.apply(pd.to_numeric, errors="coerce").sum(axis=1, min_count=1)
        partes.append(soma.to_frame(nome))
    return pd.concat(partes, axis=1)


def _alinhar_metricas(base: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    rename = {}
    for col in base.columns:
        if col in {"ANO", "ano_num", "CENA", "CONTA", "VALOR"} or _slug(col) in _ROTULOS_CENA:
            continue
        destino = resolve_account_name(col)
        if destino != str(col).strip():
            rename[col] = destino
    out = base.rename(columns=rename) if rename else base
    if rename:
        _log("info", f"Cabecalhos de metrica traduzidos: {rename}")
        out = _consolidar_duplicadas(out)
    metricas = [
        col
        for col in out.columns
        if col not in {"ANO", "ano_num", "CENA", "CONTA", "VALOR"} and _slug(col) not in _ROTULOS_CENA
    ]
    return out, metricas


def _para_longo(dados: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    base = dados.copy()
    if "ano_num" not in base.columns and "ANO" in base.columns:
        base["ano_num"] = base["ANO"].astype(str).str.extract(r"(\d+)", expand=False)
        _log("info", "Coluna opcional 'ano_num' ausente: derivada de 'ANO'.")
    if "ANO" not in base.columns and "ano_num" in base.columns:
        base["ANO"] = "Ano " + pd.to_numeric(base["ano_num"], errors="coerce").fillna(0).astype(int).astype(str)
        _log("info", "Coluna opcional 'ANO' ausente: derivada de 'ano_num'.")

    base, metricas = _alinhar_metricas(base)
    tem_eixo = "CENA" in base.columns and ("ANO" in base.columns or "ano_num" in base.columns)
    tem_longo = {"CENA", "CONTA", "VALOR"}.issubset(base.columns) or (
        {"CENA", "CONTA"}.issubset(base.columns) and not metricas
    )
    preferir_largo = tem_eixo and bool(metricas) and not tem_longo
    _log(
        "info",
        f"Detetor de formato: eixo={tem_eixo} longo_nativo={tem_longo} "
        f"metricas={metricas} → {'largo' if preferir_largo else 'longo' if tem_longo else 'incompleto'}",
    )
    if preferir_largo:
        if "ANO" not in base.columns:
            base["ANO"] = "Ano " + pd.to_numeric(base["ano_num"], errors="coerce").fillna(0).astype(int).astype(str)
        if "ano_num" not in base.columns:
            base["ano_num"] = base["ANO"].astype(str).str.extract(r"(\d+)", expand=False)
        _log("info", f"Formato largo detetado. Metricas a pivotar: {metricas}")
        longo = base.melt(id_vars=["ANO", "ano_num", "CENA"], value_vars=metricas, var_name="CONTA", value_name="VALOR")
        longo["CONTA"] = longo["CONTA"].map(resolve_account_name)
        return longo, "largo"

    if {"CENA", "CONTA"}.issubset(base.columns):
        if "VALOR" not in base.columns:
            base["VALOR"] = 0
            _log("warning", "Coluna opcional 'VALOR' ausente: preenchida com 0.")
        base["CONTA"] = base["CONTA"].map(resolve_account_name)
        return base, "longo"
    return base, "incompleto"


def _amostra(df: pd.DataFrame, mascara: pd.Series, colunas: list[str], limite: int = 5) -> str:
    recorte = df.loc[mascara, [col for col in colunas if col in df.columns]].head(limite)
    if recorte.empty:
        return ""
    return recorte.to_dict(orient="records").__repr__()


def normalizar_upload(df: pd.DataFrame, *, nome_arquivo: str = "memoria") -> tuple[pd.DataFrame, list[str]]:
    """Normaliza qualquer grade enviada para ANO/CENA/CONTA/VALOR/ano_num."""
    try:
        return _normalizar_upload(df, nome_arquivo=nome_arquivo)
    except Exception as exc:
        colunas = list(getattr(df, "columns", []))
        msg = (
            f"Falha ao normalizar '{nome_arquivo}': {type(exc).__name__}: {exc}. "
            f"Colunas detetadas: {colunas}."
        )
        _log("error", msg)
        traceback.print_exc()
        return pd.DataFrame(columns=REQUIRED_LONG_COLUMNS), [msg]


def _normalizar_upload(df: pd.DataFrame, *, nome_arquivo: str = "memoria") -> tuple[pd.DataFrame, list[str]]:
    erros: list[str] = []
    originais = list(df.columns)
    _log("info", f"Normalizando '{nome_arquivo}'. Colunas originais: {originais}")
    _log(
        "info",
        "Colunas esperadas: obrigatorias CENA + (ANO ou ano_num) + (CONTA e VALOR no formato longo "
        "ou colunas-metrica no formato largo). Opcionais: VALOR (default 0), ANO, ano_num.",
    )
    _log("info", f"Aliases estruturais aceites: {sorted(set(COLUMN_ALIASES))}")

    if df.empty:
        msg = f"A tabela de '{nome_arquivo}' esta vazia (0 linhas apos a leitura)."
        _log("error", msg)
        return pd.DataFrame(columns=REQUIRED_LONG_COLUMNS), [msg]

    dados, mapeamento = mapear_colunas(df)
    _log("info", f"Mapeamento de cabecalhos: {mapeamento}")
    _log("info", f"Colunas apos aliases: {dados.columns.tolist()}")

    dados, formato = _para_longo(dados)
    _log("info", f"Formato interpretado: {formato}. Colunas atuais: {dados.columns.tolist()}")

    ausentes = []
    if "CENA" not in dados.columns:
        ausentes.append("CENA (ex.: CENA, Cenário, ID_Cenario, scenario)")
    if "ANO" not in dados.columns and "ano_num" not in dados.columns:
        ausentes.append("ANO ou ano_num (ex.: Ano, year, periodo)")
    if "CONTA" not in dados.columns:
        ausentes.append("CONTA (formato longo) ou colunas-metrica (formato largo, ex.: Receita Bruta (R$))")
    if ausentes:
        msg = (
            f"Coluna obrigatoria nao encontrada no arquivo '{nome_arquivo}': {'; '.join(ausentes)}. "
            f"Colunas originais detetadas: {originais}."
        )
        _log("error", msg)
        erros.append(msg)
        return pd.DataFrame(columns=REQUIRED_LONG_COLUMNS), erros

    if "ano_num" not in dados.columns:
        dados["ano_num"] = dados["ANO"].astype(str).str.extract(r"(\d+)", expand=False)
    if "ANO" not in dados.columns:
        dados["ANO"] = "Ano " + pd.to_numeric(dados["ano_num"], errors="coerce").fillna(0).astype(int).astype(str)
    if "VALOR" not in dados.columns:
        dados["VALOR"] = 0
        _log("warning", "VALOR ausente apos o reshape: preenchido com 0.")

    n_inicial = len(dados)
    dados["ano_num"] = pd.to_numeric(dados["ano_num"], errors="coerce")
    dados["CENA"] = dados["CENA"].map(lambda x: "" if _eh_vazio(x) else str(x).strip())
    dados["CONTA"] = normalizar_conta(dados["CONTA"].map(lambda x: "" if _eh_vazio(x) else x))
    valor_num = _to_number(dados["VALOR"])
    falhas_valor = int(valor_num.isna().sum())
    if falhas_valor:
        aviso = (
            f"{falhas_valor} valor(es) nao numericos em 'VALOR' foram convertidos para 0 "
            f"(falha de conversao numerica). Exemplos: {_amostra(dados, valor_num.isna(), ['ANO', 'CENA', 'CONTA', 'VALOR'])}"
        )
        _log("warning", aviso)
        erros.append(aviso)
    dados["VALOR"] = valor_num.fillna(0)

    sem_ano = dados["ano_num"].isna()
    sem_cena = dados["CENA"] == ""
    sem_conta = dados["CONTA"] == ""
    if sem_ano.any():
        msg = (
            f"{int(sem_ano.sum())} linha(s) rejeitada(s): 'Ano'/'ano_num' sem numero valido. "
            f"Exemplos: {_amostra(dados, sem_ano, ['ANO', 'CENA', 'CONTA'])}"
        )
        _log("error", msg)
        erros.append(msg)
    if sem_cena.any():
        msg = (
            f"{int(sem_cena.sum())} linha(s) rejeitada(s): coluna 'CENA' vazia apos normalizacao. "
            f"Exemplos: {_amostra(dados, sem_cena, ['ANO', 'CENA', 'CONTA'])}"
        )
        _log("error", msg)
        erros.append(msg)
    if sem_conta.any():
        msg = (
            f"{int(sem_conta.sum())} linha(s) rejeitada(s): coluna 'CONTA' vazia apos normalizacao. "
            f"Exemplos: {_amostra(dados, sem_conta, ['ANO', 'CENA', 'CONTA'])}"
        )
        _log("error", msg)
        erros.append(msg)

    validos = dados.loc[~sem_ano & ~sem_cena & ~sem_conta].copy()
    validos["ano_num"] = validos["ano_num"].astype("Int64")
    _log(
        "info",
        f"Resultado '{nome_arquivo}': {len(validos)} linha(s) validas de {n_inicial} "
        f"(rejeitadas={n_inicial - len(validos)}).",
    )
    if validos.empty:
        if not erros:
            erros.append(
                f"Nenhuma linha valida foi encontrada apos a normalizacao de '{nome_arquivo}'. "
                f"Colunas originais: {originais}. Mapeamento: {mapeamento}."
            )
        _log("error", erros[-1])
    return validos[REQUIRED_LONG_COLUMNS].reset_index(drop=True), erros


def importar_planilha(nome_arquivo: str, payload: bytes) -> tuple[pd.DataFrame, list[str]]:
    """Le e normaliza um CSV/Excel enviado pelo painel."""
    try:
        cru, avisos = ler_upload(nome_arquivo, payload)
        dados, erros = normalizar_upload(cru, nome_arquivo=nome_arquivo)
        return dados, avisos + erros
    except Exception as exc:
        msg = f"Falha ao ler '{nome_arquivo}': {type(exc).__name__}: {exc}"
        _log("error", msg)
        traceback.print_exc()
        return pd.DataFrame(columns=REQUIRED_LONG_COLUMNS), [msg]
