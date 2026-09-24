"""Motor RAG: indexa cenários CTI + manuais e responde com LLM (Gemini)."""

from __future__ import annotations

import os
import re
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

load_dotenv(ROOT / "Backend" / ".env")
load_dotenv(ROOT / ".env")
load_dotenv(ROOT.parent / ".env")

SYSTEM_PROMPT_PT = (
    "Você é o Consultor Financeiro Virtual da CTI. Responda às perguntas da diretoria "
    "usando estritamente o contexto dos cenários simulados, do recorte filtrado em foco "
    "e dos documentos/manuais fornecidos. Priorize NCG, Saldo de Tesouraria, ciclo "
    "financeiro e riscos (selo, liquidez, caixa de encerramento) quando a pergunta for "
    "sobre o cenário atual. Se a informação não estiver no contexto, informe educadamente "
    "que não possui esse dado nos manuais da CTI. Seja objetivo, executivo e cite números."
)
SYSTEM_PROMPT_EN = (
    "You are CTI's Virtual Financial Advisor. Answer board-level questions using strictly "
    "the provided simulated scenarios, the filtered focus slice and CTI manuals. Prioritize "
    "NWC, treasury balance, cash cycle and risks (badge, liquidity, closing cash) when the "
    "question is about the current scenario. If the information is not in the context, "
    "politely say it is not in CTI's manuals. Be concise, executive, and cite figures."
)

_PLACEHOLDER_NAMES = {"venha para a fecap!"}
_TEXT_SUFFIXES = {".md", ".txt", ".markdown"}
_PDF_SUFFIXES = {".pdf"}
_MAX_FILE_BYTES = 12 * 1024 * 1024
_GEMINI_MODELS = ("gemini-2.0-flash", "gemini-1.5-flash", "gemini-2.5-flash")
_NOME_TRANSCRICAO = re.compile(
    r"transcri|aula|reuni[aã]o|conversa|anota[cç]|dito_na|o_que_foi",
    re.IGNORECASE,
)
_MARCA_FALA = re.compile(
    r"\b(professor|eh,|né\?|beleza|tá pensando|pode falar)\b",
    re.IGNORECASE,
)
_TERMOS_FIN = (
    "ncg",
    "tesouraria",
    "selo",
    "ebitda",
    "liquidez",
    "caixa",
    "rentabilidade",
    "ciclo",
    "risco",
    "receita",
)


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


def _parece_transcricao(path: Path, texto: str = "") -> bool:
    """Anotações de aula/reunião ficam fora do índice."""
    if _NOME_TRANSCRICAO.search(path.stem):
        return True
    amostra = texto[:2500]
    if not amostra.strip():
        return False
    return len(_MARCA_FALA.findall(amostra)) >= 3


def _iter_arquivos_doc() -> list[Path]:
    """Só o manual da CTI e documentos técnicos em Backend/documentos."""
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
        if not texto.strip() or _parece_transcricao(path, texto):
            continue
        origem = str(path.relative_to(ROOT.parent)) if ROOT.parent in path.parents else path.name
        tipo = "manual_executivo" if "manual_executivo" in path.stem.lower() else "manual"
        for chunk in splitter.split_text(texto):
            docs.append(Document(page_content=chunk, metadata={"source": origem, "tipo": tipo}))
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


def _serie_val(k: pd.Series | None, col: str) -> float:
    if k is None or col not in k.index:
        return float("nan")
    try:
        return float(k[col])
    except (TypeError, ValueError):
        return float("nan")


def build_focus_context(
    ranking: pd.DataFrame,
    *,
    cena_sel: str,
    n_cenarios: int,
    p_ruina: float,
    ano_enc: int,
    k: pd.Series | None = None,
    ano_sel: str | int = "Todos",
    lang: str = "pt",
) -> str:
    """Texto de contexto do cenário/recorte em foco (NCG, tesouraria e riscos)."""
    en = lang == "en"
    recorte_todos = str(ano_sel) in {"Todos", "All", "__all__"}
    if recorte_todos:
        recorte = "all years in the horizon" if en else "todos os anos do horizonte"
    else:
        recorte = f"Year {ano_sel}" if en else f"Ano {ano_sel}"

    ncg = _serie_val(k, "NCG")
    tes = _serie_val(k, "Saldo_Tesouraria")
    ciclo = _serie_val(k, "Ciclo_Financeiro")
    liq = _serie_val(k, "liquidez")
    rent = _serie_val(k, "rentabilidade")
    risco = _serie_val(k, "risco")
    liq_txt = f"{liq:.2f}x" if pd.notna(liq) else "—"

    if en:
        linhas = [
            f"Dashboard focus: scenario {cena_sel}; slice {recorte}; "
            f"{n_cenarios} simulated scenarios; probability of negative cash in Year {ano_enc}: {p_ruina:.1f}%.",
            "Filtered-slice indicators (NWC / Treasury / Risk): "
            f"NWC {_rs(ncg)}; treasury balance {_rs(tes)}; cash cycle {_dias(ciclo)}; "
            f"current liquidity {liq_txt}; profitability {_pct(rent)}; risk {_pct(risco)}.",
        ]
    else:
        linhas = [
            f"Foco atual do painel: cenário {cena_sel}; recorte {recorte}; "
            f"{n_cenarios} cenários simulados; prob. de caixa negativo no Ano {ano_enc}: {p_ruina:.1f}%.",
            "Indicadores do recorte filtrado (NCG / Tesouraria / Riscos): "
            f"NCG {_rs(ncg)}; saldo de tesouraria {_rs(tes)}; ciclo financeiro {_dias(ciclo)}; "
            f"liquidez corrente {liq_txt}; rentabilidade {_pct(rent)}; risco {_pct(risco)}.",
        ]

    bloco = ranking.loc[ranking["CENA"] == cena_sel] if "CENA" in ranking.columns else ranking.iloc[0:0]
    if not bloco.empty:
        row = bloco.iloc[0]
        selo = row["selo"] if "selo" in bloco.columns else "—"
        caixa = row["caixa_ano12"] if "caixa_ano12" in bloco.columns else float("nan")
        if en:
            linhas.append(
                f"Focus scenario row: badge {selo}; Year-12 cash {_rs(float(caixa)) if pd.notna(caixa) else '—'}; "
                f"NWC {_rs(float(row['NCG'])) if 'NCG' in bloco.columns else '—'}; "
                f"treasury {_rs(float(row['Saldo_Tesouraria'])) if 'Saldo_Tesouraria' in bloco.columns else '—'}."
            )
        else:
            linhas.append(
                f"Linha do cenário em foco: selo {selo}; caixa Ano 12 {_rs(float(caixa)) if pd.notna(caixa) else '—'}; "
                f"NCG {_rs(float(row['NCG'])) if 'NCG' in bloco.columns else '—'}; "
                f"tesouraria {_rs(float(row['Saldo_Tesouraria'])) if 'Saldo_Tesouraria' in bloco.columns else '—'}."
            )
    return "\n".join(linhas)


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

    def retrieve(self, query: str, k: int = 8, cena_sel: str | None = None) -> list[Document]:
        if not query.strip() or not self.documents:
            return []
        k = max(1, min(k, len(self.documents)))
        pool = min(len(self.documents), max(k * 4, 24))
        q = np.asarray([self.embeddings.embed_query(query)], dtype=np.float32)
        if self._index is not None:
            scores, idxs = self._index.search(q, pool)
            pares = [
                (float(scores[0][pos]), int(idxs[0][pos]))
                for pos in range(len(idxs[0]))
                if 0 <= int(idxs[0][pos]) < len(self.documents)
            ]
        else:
            sims = self.vectors @ q[0]
            ordem = np.argsort(-sims)[:pool]
            pares = [(float(sims[int(i)]), int(i)) for i in ordem]
        ranqueados = sorted(
            ((_prioridade_fonte(self.documents[i], score), i) for score, i in pares),
            reverse=True,
        )
        hits = [self.documents[i] for _, i in ranqueados[:k]]
        if not cena_sel:
            return hits
        ids_hit = {id(doc) for doc in hits}
        extras: list[Document] = []
        alvo = f"cenario/{cena_sel}"
        for doc in self.documents:
            src = str(doc.metadata.get("source", ""))
            tipo = str(doc.metadata.get("tipo", ""))
            if src == alvo or tipo in {"resumo", "manual_executivo"}:
                if id(doc) not in ids_hit:
                    extras.append(doc)
                    ids_hit.add(id(doc))
        return (extras + hits)[: k + 2]

    def ask(
        self,
        question: str,
        *,
        lang: str,
        history: list[dict[str, str]],
        api_key: str | None = None,
        extra_context: str = "",
        cena_sel: str | None = None,
    ) -> tuple[str, list[str]]:
        hits = self.retrieve(question, cena_sel=cena_sel)
        fontes = []
        for doc in hits:
            src = str(doc.metadata.get("source", "contexto"))
            if src not in fontes:
                fontes.append(src)
        if extra_context.strip() and "foco-atual" not in fontes:
            fontes.insert(0, "foco-atual")
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


def _prioridade_fonte(doc: Document, score: float) -> float:
    """Manual executivo e indicadores do CSV sobem na busca."""
    tipo = str(doc.metadata.get("tipo", ""))
    origem = str(doc.metadata.get("source", "")).lower()
    bonus = 0.0
    if tipo == "manual_executivo" or "manual_executivo" in origem:
        bonus += 0.45
    elif tipo == "resumo":
        bonus += 0.35
    elif tipo == "selo":
        bonus += 0.25
    elif tipo == "cenario":
        bonus += 0.12
    return score + bonus


def _paragrafos_financeiros(hits: list[Document]) -> list[str]:
    vistos: set[str] = set()
    saida: list[str] = []
    for doc in hits:
        blocos = re.split(r"\n\s*\n", doc.page_content)
        if len(blocos) == 1:
            blocos = [doc.page_content]
        for bloco in blocos:
            limpo = " ".join(bloco.split())
            baixo = limpo.lower()
            if len(limpo) < 40 or not any(termo in baixo for termo in _TERMOS_FIN):
                continue
            if _MARCA_FALA.search(limpo):
                continue
            chave = limpo[:180]
            if chave in vistos:
                continue
            vistos.add(chave)
            saida.append(limpo[:700])
            if len(saida) >= 4:
                return saida
    return saida


def _resposta_extrativa(question: str, hits: list[Document], lang: str) -> str:
    _ = question
    if lang == "en":
        titulo = "📄 Selected excerpts from CTI documentation"
        vazio = "No financial excerpt matched this question in the CTI manuals or simulated scenarios."
        dica = "💡 Tip: add GOOGLE_API_KEY to the Backend .env file for summarized analytical answers."
    else:
        titulo = "📄 Trechos Selecionados da Documentação CTI"
        vazio = "Não há trecho financeiro correspondente a essa pergunta nos manuais da CTI nem nos cenários simulados."
        dica = "💡 Dica: Adicione a GOOGLE_API_KEY no arquivo .env do Backend para respostas resumidas e analíticas pela IA."
    paragrafos = _paragrafos_financeiros(hits)
    corpo = "\n\n".join(paragrafos) if paragrafos else vazio
    return f"{titulo}\n\n{corpo}\n\n{dica}"


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
