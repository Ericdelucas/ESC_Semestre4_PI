# ele arquivo serve para formatar e exportar os relatorios de auditoria, em formato JSON ou Markdown
"""Formatacao e exportacao dos relatorios de auditoria."""

# ele importa a anotacao de futuras funcionalidades do python
from __future__ import annotations

# ele importa o modulo json, que e usado para serializar o relatorio em formato JSON
import json
# ele importa o datetime, que e usado para gerar o timestamp do relatorio
from datetime import datetime
# ele importa o Path do modulo pathlib, que e usado para manipular caminhos de arquivos
from pathlib import Path
#  ele importa Any do modulo typing, que e usado para indicar que um valor pode ser de qualquer tipo
from typing import Any

# ele faz pega esse .config, que e o modulo de configuracao da auditoria, e importa a constante REPORT_DIR, que define o diretorio onde os relatorios serao salvos
from .config import REPORT_DIR

# a função _json_default é usada para converter valores escalares do pandas/numpy para tipos nativos do JSON, como int, float ou str
def _json_default(value):
    """Converte escalares pandas/numpy para JSON nativo."""
    # verifica se o valor tem o metodo item, que e usado para extrair o valor escalar de um objeto pandas/numpy, e retorna o valor escalar
    if hasattr(value, "item"):
        return value.item()
    # e retorna o valor como string, caso nao seja um escalar
    return str(value)

# ele formata um numero no padrao brasileiro, com duas casas decimais, ponto como separador de milhar e virgula como separador decimal
def format_money(value: float | None) -> str:
    """Formata numero no padrao brasileiro."""
    # se o valor for None, retorna "n/d", caso contrario, formata o valor com duas casas decimais, substituindo os separadores de milhar e decimal
    if value is None:
        return "n/d"
    # e retorna o valor formatado com duas casas decimais, substituindo os separadores de milhar e decimal
    return f"{value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")

# essa função formata o relatorio de auditoria para exibir no terminal, com seções numeradas, indentação e alinhamento de colunas
def format_console_report(report: dict[str, Any]) -> str:
    """Formata relatorio para terminal."""
    meta = report["metadata"]
    structure = report["structure"]
    dup = report["duplicates"]
    columns = report["columns"]
    missing = report["missing_values"]
    anomalies = report["anomalies"]
    controls = report["control_totals"]
    # essa lista de linhas é usada para armazenar as linhas do relatorio formatado, que serao unidas no final com quebras de linha
    lines = [
        "",
        "========== AUDITORIA CTI ==========",
        f"Fonte: {meta['source']}",
        f"Executada em: {meta['started_at']} | duracao: {meta['duration_seconds']}s",
        f"Memoria estimada por chunk: {meta['peak_chunk_memory_mb']} MB",
        "",
        "[1] Estrutura e volume",
        f"- Linhas: {structure['rows']:,}",
        f"- Colunas esperadas: {structure['columns']} ({', '.join(structure['expected_columns'])})",
        f"- Cenarios: {structure['scenarios']:,}",
        f"- Anos detectados: {structure['years']}",
        "",
        "[2] Tipagem e parsing",
    ]
    # ele faz um loop sobre cada coluna e suas informacoes, e formata uma linha com o nome da coluna, os tipos detectados, o numero de valores nulos e o percentual de nulos, e se a coluna for VALOR ou ano_num, adiciona o valor minimo, maximo e o numero de falhas de parsing
    for col, info in columns.items():
        minmax = ""
        if col in {"VALOR", "ano_num"}:
            minmax = f" | min={info['min']} max={info['max']} falhas_parse={info['parse_failures']}"
        lines.append(f"- {col}: tipos={info['dtype_samples']} | nulls={info['nulls']} ({info['null_pct']}%){minmax}")
    # ele adiciona uma seção de duplicidades, com o numero de grupos duplicados e excedentes para linhas 100% duplicadas e por chave de negocio
    lines.extend(
        [
            "",
            "[3] Duplicidades",
            f"- Linhas 100% duplicadas: grupos={dup['full_rows']['duplicated_groups']:,}, excedentes={dup['full_rows']['extra_rows']:,}",
            f"- Chave de negocio {structure['business_key']}: grupos={dup['business_key']['duplicated_groups']:,}, excedentes={dup['business_key']['extra_rows']:,}",
            "",
            "[4] Ausentes, sujeiras e anomalias",
        ]
    )
    # ele faz um loop sobre cada coluna e suas informacoes de ausentes, sujeiras e anomalias, e formata uma linha com o nome da coluna, o numero de valores nulos, o percentual de nulos e o numero de strings vazias
    for col, info in missing["by_column"].items():
        lines.append(f"- {col}: nulls={info['nulls']:,} ({info['null_pct']}%), vazios={info['empty_strings']:,}")
    lines.extend(
        [
            f"- Exemplos criticos ausentes: {len(missing['critical_examples'])}",
            f"- Exemplos negativos inesperados: {len(anomalies['negative_where_unexpected_examples'])}",
            f"- Exemplos fora do periodo: {len(anomalies['out_of_period_examples'])}",
            f"- Exemplos de falha no parsing monetario: {len(anomalies['value_parse_error_examples'])}",
            "",
            "[5] Totais de controle",
        ]
    )
    # ele faz um loop sobre cada grupo de contas de controle e suas informacoes, e formata uma linha com o nome do grupo, a soma, a soma absoluta, a media e o numero de valores nao nulos
    for name, info in controls.items():
        lines.append(
            f"- {name}: soma={format_money(info['sum'])} | soma_abs={format_money(info['abs_sum'])} | media={format_money(info['mean'])} | n={info['non_null_values']:,}"
        )
    # essa condicional verifica se o relatorio tem um caminho de arquivo, e se tiver, adiciona uma linha indicando onde o relatorio foi salvo
    if meta.get("report_path"):
        lines.extend(["", f"Relatorio salvo em: {meta['report_path']}"])
    lines.append("===================================")
    # e retorna a string do relatorio formatado, unindo as linhas com quebras de linha
    return "\n".join(lines)


# essa função salva o relatorio de auditoria em formato JSON ou Markdown, dentro do diretorio definido em REPORT_DIR, com um timestamp no nome do arquivo
def save_audit_report(report: dict[str, Any], *, report_format: str = "json") -> Path:
    """Salva relatorio JSON ou Markdown dentro do backend."""
    REPORT_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    fmt = report_format.lower().strip()
    # ele verifica se o formato do relatorio e valido, e se nao for, levanta um ValueError
    if fmt not in {"json", "markdown", "md"}:
        raise ValueError("report_format deve ser 'json' ou 'markdown'.")
    # ele adiciona o caminho do relatorio ao dicionario de metadados do relatorio, para que seja possivel saber onde o relatorio foi salvo
    if fmt == "json":
        path = REPORT_DIR / f"auditoria_cti_{stamp}.json"
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
        return path
    path = REPORT_DIR / f"auditoria_cti_{stamp}.md"
    path.write_text(format_markdown_report(report), encoding="utf-8")
    #e retorna o caminho do arquivo salvo, para que seja possivel acessar o relatorio posteriormente
    return path

# essa função gera um relatorio resumido em formato Markdown, com seções numeradas, tabelas e listas, a partir do dicionario de relatorio de auditoria
def format_markdown_report(report: dict[str, Any]) -> str:
    #aqui ele gera o relatorio resumido em formato Markdown, com seções numeradas, tabelas e listas, a partir do dicionario de relatorio de auditoria
    """Gera relatorio Markdown resumido."""
    # esse dicionario de linhas é usado para armazenar as linhas do relatorio formatado, que serao unidas no final com quebras de linha
    lines = [
        "# Auditoria CTI",
        "",
        # esse f e usado para formatar strings com variaveis, e ele adiciona o nome da fonte do relatorio, a data e hora de execucao, o numero de linhas, cenarios e anos detectados
        f"- Fonte: `{report['metadata']['source']}`",
        f"- Executada em: `{report['metadata']['started_at']}`",
        f"- Linhas: `{report['structure']['rows']:,}`",
        f"- Cenarios: `{report['structure']['scenarios']:,}`",
        f"- Anos: `{report['structure']['years']}`",
        "",
        "## Totais de controle",
        "",
        "| Grupo | Soma | Soma absoluta | Media | N |",
        "|---|---:|---:|---:|---:|",
    ]

    # esse loop faz um iteracao sobre cada grupo de contas de controle e suas informacoes, e adiciona uma linha na tabela com o nome do grupo, a soma, a soma absoluta, a media e o numero de valores nao nulos
    for name, info in report["control_totals"].items():
        # ele adiciona uma linha na tabela com o nome do grupo, a soma, a soma absoluta, a media e o numero de valores nao nulos, formatando os numeros com a funcao format_money e adicionando separadores de milhar
        lines.append(
            f"| {name} | {format_money(info['sum'])} | {format_money(info['abs_sum'])} | {format_money(info['mean'])} | {info['non_null_values']:,} |"
        )
    # esse extend adiciona mais linhas no relatorio, com as seções de duplicidades e regras de tratamento, e o numero de linhas duplicadas e excedentes para linhas 100% duplicadas e por chave de negocio    
    lines.extend(
        [
            "",
            "## Duplicidades",
            "",
            f"- Linhas 100% duplicadas: `{report['duplicates']['full_rows']['extra_rows']:,}` excedentes.",
            f"- Chave de negocio: `{report['duplicates']['business_key']['extra_rows']:,}` excedentes.",
            "",
            "## Regras de tratamento",
            "",
        ]
    )
    # esse loop faz uma iteracao sobre cada campo e sua regra de imputacao, e adiciona uma linha na lista de linhas com o nome do campo e a regra de imputacao
    for field_name, rule in report["missing_values"]["imputation_rules"].items():
        lines.append(f"- **{field_name}:** {rule}")
        # e retorna a string do relatorio formatado, unindo as linhas com quebras de linha
    return "\n".join(lines) + "\n"

