"""Construcao dos documentos usados pelo RAG."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from src.config import DOCS_DIR, REPO_DOCS_DIR, ROOT
from src.config.glossary import GLOSSARIO

from .config import (
    MARCA_FALA,
    MAX_FILE_BYTES,
    NOME_TRANSCRICAO,
    PDF_SUFFIXES,
    PLACEHOLDER_NAMES,
    TEXT_SUFFIXES,
)
from .formatters import dias, pct, rs


def ler_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    partes: list[str] = []
    for page in reader.pages:
        texto = page.extract_text() or ""
        if texto.strip():
            partes.append(texto)
    return "\n".join(partes)


def parece_transcricao(path: Path, texto: str = "") -> bool:
    """Anotacoes de aula/reuniao ficam fora do indice."""
    if NOME_TRANSCRICAO.search(path.stem):
        return True
    amostra = texto[:2500]
    if not amostra.strip():
        return False
    return len(MARCA_FALA.findall(amostra)) >= 3


def iter_arquivos_doc() -> list[Path]:
    """Arquivos tecnicos em Backend/documentos e na pasta documentos do repositorio."""
    candidatos: list[Path] = []
    pastas = [
        DOCS_DIR,
        REPO_DOCS_DIR,
    ]
    for alvo in pastas:
        if alvo.is_file():
            candidatos.append(alvo)
            continue
        if not alvo.is_dir():
            continue
        for path in alvo.rglob("*"):
            if path.is_file():
                candidatos.append(path)
    vistos: set[Path] = set()
    unicos: list[Path] = []
    for path in candidatos:
        resolved = path.resolve()
        if resolved in vistos:
            continue
        vistos.add(resolved)
        if path.suffix.lower() not in TEXT_SUFFIXES | PDF_SUFFIXES:
            continue
        if path.stem.strip().lower() in PLACEHOLDER_NAMES:
            continue
        if path.name.lower() == "base_conhecimento_cti.md":
            continue
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                continue
        except OSError:
            continue
        unicos.append(path)
    return unicos


def docs_manuais() -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=900, chunk_overlap=120)
    docs: list[Document] = []
    for path in iter_arquivos_doc():
        try:
            if path.suffix.lower() in PDF_SUFFIXES:
                texto = ler_pdf(path)
            else:
                texto = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if not texto.strip() or parece_transcricao(path, texto):
            continue
        origem = str(path.relative_to(ROOT.parent)) if ROOT.parent in path.parents else path.name
        stem = path.stem.lower()
        if path.parent.resolve() == REPO_DOCS_DIR.resolve() and path.suffix.lower() in TEXT_SUFFIXES:
            tipo = "base_conhecimento"
        elif "base_conhecimento_cti" in stem:
            tipo = "base_conhecimento"
        elif "manual_executivo" in stem:
            tipo = "manual_executivo"
        else:
            tipo = "manual"
        for chunk in splitter.split_text(texto):
            docs.append(Document(page_content=chunk, metadata={"source": origem, "tipo": tipo}))
    return docs


def status_documentos() -> dict[str, object]:
    """Resume os arquivos tecnicos disponiveis para o indice RAG."""
    arquivos = iter_arquivos_doc()
    return {
        "count": len(arquivos),
        "sources": [str(path.relative_to(ROOT.parent)) if ROOT.parent in path.parents else path.name for path in arquivos],
        "directories": [str(DOCS_DIR), str(REPO_DOCS_DIR)],
        "suffixes": sorted(TEXT_SUFFIXES | PDF_SUFFIXES),
    }


def docs_glossario() -> list[Document]:
    linhas = ["Glossário financeiro CTI (PT-BR e EN-US)."]
    for lang, bucket in GLOSSARIO.items():
        linhas.append(f"\nIdioma: {lang}")
        for chave, texto in bucket.items():
            linhas.append(f"- {chave}: {texto}")
    return [
        Document(
            page_content="\n".join(linhas),
            metadata={"source": "glossary.py", "tipo": "glossario"},
        )
    ]


def docs_cenarios(ranking: pd.DataFrame) -> list[Document]:
    docs: list[Document] = []
    if ranking.empty:
        return docs
    n = int(ranking.shape[0])
    caixa = ranking["caixa_ano12"] if "caixa_ano12" in ranking.columns else pd.Series(dtype=float)
    p_ruina = float((caixa < 0).mean() * 100) if not caixa.empty else 0.0
    med_caixa = float(caixa.median()) if not caixa.empty else float("nan")
    selos = ranking["selo"].value_counts() if "selo" in ranking.columns else pd.Series(dtype=int)
    linhas_selo = "\n".join(f"- {nome}: {int(qtd)} cenários" for nome, qtd in selos.items())
    resumo = (
        f"Resumo executivo dos {n} cenários simulados da CTI no horizonte de 12 anos.\n"
        f"Probabilidade de caixa negativo no Ano 12: {p_ruina:.1f}%.\n"
        f"Mediana do caixa de encerramento: {rs(med_caixa)}.\n"
        f"NCG média: {rs(float(ranking['NCG'].mean()))}.\n"
        f"Saldo de Tesouraria médio: {rs(float(ranking['Saldo_Tesouraria'].mean()))}.\n"
        f"Ciclo financeiro médio: {dias(float(ranking['Ciclo_Financeiro'].mean()))}.\n"
        f"Liquidez corrente média: {float(ranking['liquidez'].mean()):.2f}x.\n"
        f"Rentabilidade média: {pct(float(ranking['rentabilidade'].mean()))}.\n"
        f"Distribuição por selo de risco:\n{linhas_selo}\n"
        "Fórmulas: NCG = ACO − PCO; Saldo de Tesouraria = Disponível − Empréstimos CP; "
        "Ciclo Financeiro = PMR + PME − PMP; Liquidez corrente = Ativo circulante / Passivo circulante."
    )
    docs.append(Document(page_content=resumo, metadata={"source": "indicadores/resumo", "tipo": "resumo"}))

    if "selo" in ranking.columns:
        for selo, bloco in ranking.groupby("selo"):
            p_selo = float((bloco["caixa_ano12"] < 0).mean() * 100) if "caixa_ano12" in bloco else 0.0
            texto = (
                f"Selo de negócio: {selo}. Quantidade: {len(bloco)} de {n} cenários "
                f"({100 * len(bloco) / n:.1f}%). "
                f"Rentabilidade média {pct(float(bloco['rentabilidade'].mean()))}; "
                f"liquidez {float(bloco['liquidez'].mean()):.2f}x; "
                f"risco {pct(float(bloco['risco'].mean()))}; "
                f"NCG {rs(float(bloco['NCG'].mean()))}; "
                f"tesouraria {rs(float(bloco['Saldo_Tesouraria'].mean()))}; "
                f"ciclo {dias(float(bloco['Ciclo_Financeiro'].mean()))}; "
                f"prob. caixa negativo Ano 12 neste selo: {p_selo:.1f}%."
            )
            docs.append(
                Document(
                    page_content=texto,
                    metadata={"source": f"indicadores/selo/{selo}", "tipo": "selo"},
                )
            )

    for _, row in ranking.iterrows():
        cena = str(row["CENA"])
        texto = (
            f"Cenário {cena}. "
            f"Selo: {row.get('selo', '—')}. "
            f"Rentabilidade {pct(float(row['rentabilidade']))}; "
            f"liquidez {float(row['liquidez']):.2f}x; "
            f"risco {pct(float(row['risco']))}; "
            f"NCG {rs(float(row['NCG']))}; "
            f"Saldo de Tesouraria {rs(float(row['Saldo_Tesouraria']))}; "
            f"Ciclo Financeiro {dias(float(row['Ciclo_Financeiro']))}; "
            f"caixa Ano 12 {rs(float(row['caixa_ano12'])) if pd.notna(row.get('caixa_ano12')) else '—'}; "
            f"resultado médio {rs(float(row['resultado'])) if pd.notna(row.get('resultado')) else '—'}."
        )
        docs.append(Document(page_content=texto, metadata={"source": f"cenario/{cena}", "tipo": "cenario"}))
    return docs
