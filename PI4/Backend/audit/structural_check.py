# esse arquivo define as funcoes de auditoria da base CTI, que leem os dados em chunks, atualizam os acumuladores de contadores e perfis, e geram um relatorio estruturado com as informacoes coletadas
"""Verificacao estrutural: leitura, colunas, tipos, nulos e anomalias."""

# ele importa a anotacao de futuras funcionalidades do python
from __future__ import annotations
# ele importa o Path do modulo pathlib, que e usado para manipular caminhos de arquivos
from typing import Any, Iterable
# ele importa o pandas, que e usado para manipular os dados da auditoria
import pandas as pd
# ele importa a funcao normalizar_conta e parse_valor_br do modulo data_loader, que sao usadas para normalizar os nomes das contas e converter os valores monetarios do formato brasileiro para float
from Backend.data_loader import normalizar_conta, parse_valor_br

# ele importa as constantes CRITICAL_VALUE_ACCOUNTS, EXPECTED_COLUMNS e EXPECTED_NON_NEGATIVE_ACCOUNTS do modulo de configuracao da auditoria, que definem as contas criticas, as colunas esperadas e as contas que nao devem ter valores negativos
from .config import (
    CRITICAL_VALUE_ACCOUNTS,
    EXPECTED_COLUMNS,
    EXPECTED_NON_NEGATIVE_ACCOUNTS,
)
# o .models importa a classe AuditAccumulator, que representa o estado incremental da auditoria em chunks, e armazena contadores de linhas, colunas, memoria, perfis de colunas, contadores de duplicidade, contadores de contas, conjuntos de cenarios e anos vistos, e exemplos de erros
from .models import AuditAccumulator

# e uma funcao que serializa exemplos pequenos sem valores pandas nao JSON, limitando o numero de exemplos retornados
def sample_records(df: pd.DataFrame, limit: int = 5) -> list[dict[str, Any]]:
    """Serializa exemplos pequenos sem valores pandas nao JSON."""
    # ele verifica se o dataframe esta vazio, e se estiver, ele retorna uma lista vazia
    if df.empty:
        # e retorna uma lista vazia, pois nao ha exemplos para serializar
        return []
    sample = df.head(limit).astype(object)
    records = sample.where(pd.notna(sample), None).to_dict(orient="records")
    # ele retorna uma lista de dicionarios, onde cada dicionario representa uma linha do dataframe, com as chaves sendo os nomes das colunas e os valores sendo os valores das celulas, convertidos para tipos nativos do Python
    return [{str(k): v for k, v in record.items()} for record in records]

# uma funcao que le o arquivo CSV em chunks, com tratamento de erros claro
def read_csv_chunks(path, chunksize: int) -> Iterable[pd.DataFrame]:
    """Le CSV CTI em chunks com tratamento de erros claro."""
    # ele verifica se o caminho do arquivo existe, e se nao existir, ele levanta um FileNotFoundError com uma mensagem informando que o arquivo base nao foi encontrado
    if not path.exists():
        raise FileNotFoundError(f"Arquivo base nao encontrado: {path}")
    # e agora roda um try para tentar ler o arquivo CSV em chunks, usando a funcao pd.read_csv do pandas, com os parametros de cabecalho, nomes das colunas, tipo de dados, engine, tamanho do chunk e memoria baixa, e se ocorrer algum erro de dados vazios ou de encoding, ele levanta um ValueError com uma mensagem informando o erro ocorrido 
    try:
        yield from pd.read_csv(
            path,
            header=None,
            names=EXPECTED_COLUMNS,
            dtype=str,
            engine="c",
            chunksize=chunksize,
            low_memory=False,
        )
    # o except serve para capturar os erros de dados vazios e de encoding, e levantar um ValueError com uma mensagem informando o erro ocorrido
    except pd.errors.EmptyDataError as exc:
        raise ValueError(f"Arquivo CSV vazio: {path}") from exc
    except UnicodeDecodeError as exc:
        raise ValueError(f"Falha de encoding ao ler CSV: {path}") from exc

# essa funcao le uma tabela SQL em chunks via SQLAlchemy, usando a funcao pd.read_sql_query do pandas, com os parametros de conexao, consulta SQL e tamanho do chunk, e se ocorrer algum erro de conexao ou de consulta, ele levanta um RuntimeError com uma mensagem informando o erro ocorrido
def read_sql_chunks(db_url: str, table: str, chunksize: int) -> Iterable[pd.DataFrame]:
    """Le uma tabela SQL em chunks via SQLAlchemy."""
    # e roda um try para tentar importar o create_engine e text do modulo sqlalchemy, e se ocorrer um ImportError, ele levanta um RuntimeError com uma mensagem informando que e necessario instalar o sqlalchemy e o driver do banco
    try:
        from sqlalchemy import create_engine, text
    except ImportError as exc:
        raise RuntimeError(
            "Para auditar PostgreSQL/Supabase, instale sqlalchemy e o driver do banco "
            "(ex.: psycopg2-binary ou psycopg)."
        ) from exc
    # e roda um try para tentar criar uma conexao com o banco de dados usando a funcao create_engine do sqlalchemy, e se ocorrer algum erro de conexao ou de consulta, ele levanta um RuntimeError com uma mensagem informando o erro ocorrido
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            yield from pd.read_sql_query(text(f"SELECT * FROM {table}"), conn, chunksize=chunksize)
    except Exception as exc:
        raise RuntimeError(f"Falha ao ler tabela SQL '{table}': {exc}") from exc

# essa funcao prepara um chunk de dados do arquivo CTI, normalizando os nomes das colunas, convertendo as datas de ano e os valores monetarios, e adicionando uma coluna com o ano numerico extraido da coluna ANO
def prepare_cti_chunk(chunk: pd.DataFrame) -> pd.DataFrame:
    """Normaliza nomes, datas de ano e valores monetarios."""
    chunk = chunk.rename(columns={col: str(col).upper() for col in chunk.columns})
    missing = [col for col in EXPECTED_COLUMNS if col not in chunk.columns]
    # e agora ele verifica se ha colunas ausentes no chunk, e se houver, ele levanta um KeyError com uma mensagem informando quais colunas estao ausentes
    if missing:
        raise KeyError(f"Colunas esperadas ausentes: {', '.join(missing)}")
    # o out e uma copia do chunk com as colunas esperadas, e ele normaliza os nomes das contas, converte os valores monetarios para float, e extrai o ano numerico da coluna ANO usando expressao regular
    out = chunk[EXPECTED_COLUMNS].copy()
    out["ANO"] = out["ANO"].astype("string").str.strip()
    out["CENA"] = out["CENA"].astype("string").str.strip()
    out["CONTA"] = normalizar_conta(out["CONTA"])
    out["VALOR_RAW"] = out["VALOR"]
    out["VALOR"] = (
        pd.to_numeric(out["VALOR"], errors="coerce")
        if pd.api.types.is_numeric_dtype(out["VALOR"])
        else parse_valor_br(out["VALOR"])
    )
    out["ano_num"] = pd.to_numeric(out["ANO"].str.extract(r"(\d+)", expand=False), errors="coerce")
    # e ele retorna o chunk preparado, com as colunas normalizadas, os valores convertidos e o ano numerico extraido
    return out

# essa funcao atualiza os perfis de tipos, nulos e limites numericos das colunas do chunk, acumulando as informacoes no acumulador de auditoria
def update_profiles(acc: AuditAccumulator, chunk: pd.DataFrame) -> None:
    """Acumula perfil de tipos, nulos e limites numericos."""
    acc.rows += len(chunk)
    acc.columns = list(chunk.columns)
    acc.memory_bytes_estimate = max(acc.memory_bytes_estimate, int(chunk.memory_usage(deep=True).sum()))
    # e agora ele faz um loop sobre cada coluna esperada e a coluna ano_num, e para cada coluna ele atualiza o perfil de tipos, nulos e limites numericos no acumulador de auditoria, contando os valores nulos, strings vazias, falhas de parse e limites minimos e maximos
    for col in EXPECTED_COLUMNS + ["ano_num"]:
        if col not in chunk.columns:
            continue
        profile = acc.column_profiles[col]
        series = chunk[col]
        profile.nulls += int(series.isna().sum())
        if series.dtype == object or str(series.dtype).startswith("string"):
            profile.empty_strings += int(series.astype("string").str.strip().eq("").fillna(False).sum())
        profile.dtype_samples[str(series.dtype)] += len(series)
        if col in {"VALOR", "ano_num"}:
            profile.parse_failures += int(series.isna().sum())
            numeric = pd.to_numeric(series, errors="coerce").dropna()
            if not numeric.empty:
                min_val = float(numeric.min())
                max_val = float(numeric.max())
                profile.min_value = min_val if profile.min_value is None else min(profile.min_value, min_val)
                profile.max_value = max_val if profile.max_value is None else max(profile.max_value, max_val)

# e aqui ele define a funcao update_duplicates, que atualiza os contadores de duplicidade de linhas e por chave de negocio no acumulador de auditoria, contando as ocorrencias de cada linha completa e de cada chave de negocio formada pelas colunas ANO, CENA e CONTA
def update_anomalies(
    acc: AuditAccumulator,
    chunk: pd.DataFrame,
    concession_year_min: int,
    concession_year_max: int,
    sample_limit: int,
) -> None:
    """Registra exemplos de ausentes criticos, negativos e periodos invalidos."""
    critical_mask = chunk["CONTA"].isin(CRITICAL_VALUE_ACCOUNTS)
    missing_critical = chunk.loc[
        critical_mask
        & (
            chunk["VALOR"].isna()
            | chunk["ANO"].isna()
            | chunk["CENA"].isna()
            | chunk["CONTA"].isna()
            | chunk["ano_num"].isna()
        ),
        EXPECTED_COLUMNS + ["ano_num"],
    ]
    # e agora ele verifica se o numero de exemplos de ausentes criticos no acumulador de auditoria e menor que o limite de amostra, e se for, ele adiciona mais exemplos do chunk atual ate atingir o limite
    if len(acc.missing_critical_examples) < sample_limit:
        acc.missing_critical_examples.extend(sample_records(missing_critical, sample_limit - len(acc.missing_critical_examples)))
    # e agora ele filtra as linhas do chunk que tem contas que nao devem ter valores negativos e que tem valor menor que zero, e se o numero de exemplos de negativos inesperados no acumulador de auditoria e menor que o limite de amostra, ele adiciona mais exemplos do chunk atual ate atingir o limite
    negative_rows = chunk.loc[
        chunk["CONTA"].isin(EXPECTED_NON_NEGATIVE_ACCOUNTS) & (chunk["VALOR"] < 0),
        EXPECTED_COLUMNS + ["ano_num"],
    ]
    # e agora ele filtra as linhas do chunk que tem ano numerico ausente ou fora do horizonte de concessao, e se o numero de exemplos de fora do periodo no acumulador de auditoria e menor que o limite de amostra, ele adiciona mais exemplos do chunk atual ate atingir o limite
    if len(acc.negative_unexpected_examples) < sample_limit:
        acc.negative_unexpected_examples.extend(sample_records(negative_rows, sample_limit - len(acc.negative_unexpected_examples)))

    out_period_rows = chunk.loc[
        chunk["ano_num"].isna() | ~chunk["ano_num"].between(concession_year_min, concession_year_max, inclusive="both"),
        EXPECTED_COLUMNS + ["ano_num"],
    ]
    if len(acc.out_of_period_examples) < sample_limit:
        acc.out_of_period_examples.extend(sample_records(out_period_rows, sample_limit - len(acc.out_of_period_examples)))

    parse_error_rows = chunk.loc[chunk["VALOR"].isna(), ["ANO", "CENA", "CONTA", "VALOR_RAW"]]
    if len(acc.parse_error_examples) < sample_limit:
        acc.parse_error_examples.extend(sample_records(parse_error_rows, sample_limit - len(acc.parse_error_examples)))

# e agora ele define a funcao summarize_columns, que gera um resumo de qualidade por coluna a partir dos perfis acumulados no acumulador de auditoria, calculando a porcentagem de nulos, strings vazias, falhas de parse e limites minimos e maximos para cada coluna
def summarize_columns(acc: AuditAccumulator) -> dict[str, Any]:
    """Gera resumo de qualidade por coluna."""
    out: dict[str, Any] = {}
    # e agora ele faz um loop sobre cada coluna e seu perfil acumulado no acumulador de auditoria, e para cada coluna ele calcula a porcentagem de nulos, strings vazias, falhas de parse e limites minimos e maximos, e armazena essas informacoes no dicionario out
    for col, profile in acc.column_profiles.items():
        out[col] = {
            "dtype_samples": dict(profile.dtype_samples),
            "nulls": profile.nulls,
            "null_pct": round((profile.nulls / acc.rows) * 100, 4) if acc.rows else 0.0,
            "empty_strings": profile.empty_strings,
            "parse_failures": profile.parse_failures if col in {"VALOR", "ano_num"} else 0,
            "min": profile.min_value,
            "max": profile.max_value,
        }
        # e retorna o dicionario out com o resumo de qualidade por coluna, que pode ser usado para gerar relatorios ou visualizacoes
    return out

# e agora ele define a funcao update_accounts, que atualiza os contadores de contas, cenarios e anos vistos no acumulador de auditoria, contando as ocorrencias de cada conta, cenario e ano numerico no chunk atual, e acumulando os totais, somas absolutas, contagens de valores nao nulos e contagens de valores nulos por conta individual
def imputation_rules() -> dict[str, str]:
    """Regras metodologicas para ausentes."""
    # e retorna um dicionario com as regras de imputacao para cada campo, que podem ser usadas para orientar a correcao de ausentes ou anomalias nos dados
    return {
        "VALOR em conta critica": "Nao imputar automaticamente; bloquear reconciliacao e corrigir na origem ou justificar ajuste tecnico.",
        "VALOR em conta nao critica": "Manter NaN no relatorio; o pipeline analitico atual converte para 0 apenas depois da leitura controlada.",
        "ANO/CENA/CONTA ausente": "Descartar ou corrigir na origem, pois compoe chave de negocio.",
        "ANO fora do horizonte": "Descartar do dashboard ate validacao do periodo de concessao.",
    }

