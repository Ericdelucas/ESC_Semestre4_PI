"""Motor RAG: indexa cenários CTI + manuais e responde com LLM (Gemini)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from google import genai
from google.genai import types
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer

try:
    import faiss
except ImportError:
    faiss = None

from src.config import DOCS_DIR, REPO_DOCS_DIR, ROOT
from src.config.glossary import GLOSSARIO

load_dotenv(ROOT / ".env")
load_dotenv(ROOT.parent / ".env")

SYSTEM_PROMPT_PT = (
    "Você é o Consultor Financeiro Virtual da CTI. Responda às perguntas da diretoria "
    "usando estritamente o contexto dos cenários simulados e documentos fornecidos. "
    "Se a informação não estiver no contexto, informe educadamente que não possui esse "
    "dado nos manuais da CTI. Seja objetivo, executivo e cite números quando existirem."
)
SYSTEM_PROMPT_EN = (
    "You are CTI's Virtual Financial Advisor. Answer board-level questions using strictly "
    "the provided simulated scenarios and documents. If the information is not in the "
    "context, politely say it is not in CTI's manuals. Be concise, executive, and cite "
    "figures when they exist."
)

_PLACEHOLDER_NAMES = {"venha para a fecap!"}
_TEXT_SUFFIXES = {".md", ".txt", ".markdown"}
_PDF_SUFFIXES = {".pdf"}
_MAX_FILE_BYTES = 12 * 1024 * 1024
_GEMINI_MODELS = ("gemini-2.0-flash", "gemini-1.5-flash", "gemini-2.5-flash")


class TfidfEmbeddings(Embeddings):
    """Embeddings locais (TF-IDF) para o FAISS — sem depender de API para o retrieval."""

    def __init__(self, max_features: int = 768) -> None:
        self._vectorizer = TfidfVectorizer(
            max_features=max_features,
            ngram_range=(1, 2),
            min_df=1,
            lowercase=True,
        )
        self._fitted = False

    def fit(self, texts: list[str]) -> None:
        corpus = texts if texts else ["cti"]
        self._vectorizer.fit(corpus)
        self._fitted = True

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not self._fitted:
            self.fit(texts)
        matrix = self._vectorizer.transform(texts)
        dense = np.asarray(matrix.toarray(), dtype=np.float32)
        norms = np.linalg.norm(dense, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1.0, norms)
        return (dense / norms).tolist()

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]


def resolve_api_key(explicit: str | None = None) -> str | None:
    if explicit and explicit.strip():
        return explicit.strip()
    for name in ("GOOGLE_API_KEY", "GEMINI_API_KEY"):
        val = os.environ.get(name, "").strip()
        if val:
            return val
    return None


def _rs(x: float) -> str:
    if pd.isna(x):
        return "—"
    v = float(x)
    sinal = "-" if v < 0 else ""
    a = abs(v)
    if a >= 1e9:
        return f"{sinal}R$ {a / 1e9:.2f} bi"
    if a >= 1e6:
        return f"{sinal}R$ {a / 1e6:.2f} mi"
    return f"{sinal}R$ {a:,.0f}"


def _pct(x: float) -> str:
    if pd.isna(x):
        return "—"
    return f"{float(x) * 100:.2f}%"


def _dias(x: float) -> str:
    if pd.isna(x):
        return "—"
    return f"{float(x):.1f} dias"


def _ler_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    partes: list[str] = []
    for page in reader.pages:
        texto = page.extract_text() or ""
        if texto.strip():
            partes.append(texto)
    return "\n".join(partes)


def _iter_arquivos_doc() -> list[Path]:
    candidatos: list[Path] = []
    pastas = [
        DOCS_DIR,
        REPO_DOCS_DIR,
        ROOT / "README.md",
        ROOT.parent / "Estudo_do_caso" / "Oque_fazer",
        ROOT.parent / "Estudo_do_caso" / "templeit_PI",
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
        if path.suffix.lower() not in _TEXT_SUFFIXES | _PDF_SUFFIXES:
            continue
        if path.stem.strip().lower() in _PLACEHOLDER_NAMES:
            continue
        try:
            if path.stat().st_size > _MAX_FILE_BYTES:
                continue
        except OSError:
            continue
        unicos.append(path)
    return unicos


def _docs_manuais() -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=900, chunk_overlap=120)
    docs: list[Document] = []
    for path in _iter_arquivos_doc():
        try:
            if path.suffix.lower() in _PDF_SUFFIXES:
                texto = _ler_pdf(path)
            else:
                texto = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if not texto.strip():
            continue
        origem = str(path.relative_to(ROOT.parent)) if ROOT.parent in path.parents else path.name
        for chunk in splitter.split_text(texto):
            docs.append(Document(page_content=chunk, metadata={"source": origem, "tipo": "manual"}))
    return docs


def _docs_glossario() -> list[Document]:
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


def _docs_cenarios(ranking: pd.DataFrame) -> list[Document]:
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
        f"Mediana do caixa de encerramento: {_rs(med_caixa)}.\n"
        f"NCG média: {_rs(float(ranking['NCG'].mean()))}.\n"
        f"Saldo de Tesouraria médio: {_rs(float(ranking['Saldo_Tesouraria'].mean()))}.\n"
        f"Ciclo financeiro médio: {_dias(float(ranking['Ciclo_Financeiro'].mean()))}.\n"
        f"Liquidez corrente média: {float(ranking['liquidez'].mean()):.2f}x.\n"
        f"Rentabilidade média: {_pct(float(ranking['rentabilidade'].mean()))}.\n"
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
                f"Rentabilidade média {_pct(float(bloco['rentabilidade'].mean()))}; "
                f"liquidez {float(bloco['liquidez'].mean()):.2f}x; "
                f"risco {_pct(float(bloco['risco'].mean()))}; "
                f"NCG {_rs(float(bloco['NCG'].mean()))}; "
                f"tesouraria {_rs(float(bloco['Saldo_Tesouraria'].mean()))}; "
                f"ciclo {_dias(float(bloco['Ciclo_Financeiro'].mean()))}; "
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
            f"Rentabilidade {_pct(float(row['rentabilidade']))}; "
            f"liquidez {float(row['liquidez']):.2f}x; "
            f"risco {_pct(float(row['risco']))}; "
            f"NCG {_rs(float(row['NCG']))}; "
            f"Saldo de Tesouraria {_rs(float(row['Saldo_Tesouraria']))}; "
            f"Ciclo Financeiro {_dias(float(row['Ciclo_Financeiro']))}; "
            f"caixa Ano 12 {_rs(float(row['caixa_ano12'])) if pd.notna(row.get('caixa_ano12')) else '—'}; "
            f"resultado médio {_rs(float(row['resultado'])) if pd.notna(row.get('resultado')) else '—'}."
        )
        docs.append(Document(page_content=texto, metadata={"source": f"cenario/{cena}", "tipo": "cenario"}))
    return docs


def _faiss_index(vectors: np.ndarray) -> Any:
    if faiss is None:
        raise RuntimeError("faiss-cpu não instalado")
    index = faiss.IndexFlatIP(int(vectors.shape[1]))
    index.add(vectors)
    return index


@dataclass
class RagEngine:
    documents: list[Document]
    embeddings: TfidfEmbeddings
    vectors: np.ndarray
    backend: str
    _index: object | None = field(default=None, repr=False)

    @classmethod
    def from_ranking(cls, ranking: pd.DataFrame) -> RagEngine:
        docs = _docs_cenarios(ranking) + _docs_glossario() + _docs_manuais()
        if not docs:
            docs = [Document(page_content="Base CTI sem documentos.", metadata={"source": "vazio"})]
        texts = [d.page_content for d in docs]
        emb = TfidfEmbeddings()
        emb.fit(texts)
        vectors = np.asarray(emb.embed_documents(texts), dtype=np.float32)
        backend = "numpy"
        index = None
        try:
            index = _faiss_index(vectors)
            backend = "faiss"
        except Exception:
            index = None
        return cls(documents=docs, embeddings=emb, vectors=vectors, backend=backend, _index=index)

    def retrieve(self, query: str, k: int = 8) -> list[Document]:
        if not query.strip() or not self.documents:
            return []
        k = max(1, min(k, len(self.documents)))
        q = np.asarray([self.embeddings.embed_query(query)], dtype=np.float32)
        if self._index is not None:
            _scores, idxs = self._index.search(q, k)
            escolhidos = [int(i) for i in idxs[0] if 0 <= int(i) < len(self.documents)]
        else:
            sims = self.vectors @ q[0]
            escolhidos = [int(i) for i in np.argsort(-sims)[:k]]
        return [self.documents[i] for i in escolhidos]

    def ask(
        self,
        question: str,
        *,
        lang: str,
        history: list[dict[str, str]],
        api_key: str | None = None,
        extra_context: str = "",
    ) -> tuple[str, list[str]]:
        hits = self.retrieve(question)
        fontes = []
        for doc in hits:
            src = str(doc.metadata.get("source", "contexto"))
            if src not in fontes:
                fontes.append(src)
        contexto = "\n\n".join(
            f"Fonte: {doc.metadata.get('source', 'contexto')}\n{doc.page_content}" for doc in hits
        )
        if extra_context.strip():
            contexto = extra_context.strip() + "\n\n" + contexto
        chave = resolve_api_key(api_key)
        if not chave:
            return _resposta_extrativa(question, hits, lang), fontes
        resposta = _gerar_llm(question, contexto, lang, history, chave)
        return resposta, fontes


def _resposta_extrativa(question: str, hits: list[Document], lang: str) -> str:
    if not hits:
        if lang == "en":
            return "I do not have that information in CTI's manuals or simulated scenarios."
        return "Não possui esse dado nos manuais da CTI nem nos cenários simulados indexados."
    trechos = "\n\n".join(f"• {doc.page_content[:500]}" for doc in hits[:4])
    if lang == "en":
        return (
            "No Gemini API key is configured, so this is a retrieval-only excerpt from CTI materials.\n\n"
            f"Question: {question}\n\n{trechos}"
        )
    return (
        "Chave da API Gemini não configurada — segue um recorte recuperado dos materiais da CTI.\n\n"
        f"Pergunta: {question}\n\n{trechos}"
    )


def _gerar_llm(
    question: str,
    contexto: str,
    lang: str,
    history: list[dict[str, str]],
    api_key: str,
) -> str:
    client = genai.Client(api_key=api_key)
    system = SYSTEM_PROMPT_EN if lang == "en" else SYSTEM_PROMPT_PT
    idioma = "English" if lang == "en" else "português brasileiro"
    hist = history[-6:]
    linhas_hist = []
    for msg in hist:
        papel = "Diretoria" if msg.get("role") == "user" else "Consultor"
        linhas_hist.append(f"{papel}: {msg.get('content', '')}")
    historico = "\n".join(linhas_hist) if linhas_hist else "(sem histórico)"
    prompt = (
        f"Idioma da resposta: {idioma}.\n\n"
        f"Histórico recente:\n{historico}\n\n"
        f"Contexto recuperado (cenários e manuais):\n{contexto}\n\n"
        f"Pergunta: {question}"
    )
    ultimo_erro: Exception | None = None
    for modelo in _GEMINI_MODELS:
        try:
            resp = client.models.generate_content(
                model=modelo,
                contents=prompt,
                config=types.GenerateContentConfig(system_instruction=system),
            )
            texto = (resp.text or "").strip()
            if texto:
                return texto
        except Exception as exc:  # noqa: BLE001 — tenta o próximo modelo
            ultimo_erro = exc
            continue
    if lang == "en":
        return f"Could not generate an answer with Gemini: {ultimo_erro}"
    return f"Não foi possível gerar a resposta com o Gemini: {ultimo_erro}"
