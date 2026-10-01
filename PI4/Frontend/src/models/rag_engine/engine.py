"""Classe principal do motor RAG e retrieval."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd
from langchain_core.documents import Document

try:
    import faiss
except ImportError:
    faiss = None

from .answers import gerar_llm, resolve_api_key
from .documents import docs_cenarios, docs_glossario, docs_manuais
from .embeddings import TfidfEmbeddings


def faiss_index(vectors: np.ndarray) -> Any:
    if faiss is None:
        raise RuntimeError("faiss-cpu não instalado")
    index = faiss.IndexFlatIP(int(vectors.shape[1]))
    index.add(vectors)
    return index


def prioridade_fonte(doc: Document, score: float) -> float:
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


def _resposta_sem_llm(question: str, extra_context: str, lang: str) -> str:
    pergunta = unicodedata.normalize("NFKD", question.lower()).encode("ascii", "ignore").decode("ascii")
    fechamento = (
        "Gostaria que eu direcionasse você para a aba de DRE/EBITDA ou quer analisar outro indicador?"
        if lang != "en"
        else "Would you like me to take you to the DRE/EBITDA tab, or would you rather analyze another indicator?"
    )
    if re.search(r"\b(o que e|o que é|what is|api)\b", pergunta) and "api" in pergunta:
        if lang == "en":
            return (
                "An API is a defined way for systems to communicate, exposing functions or data "
                "through documented requests and responses. Would you like to connect this idea "
                "to the CTI dashboard data flow, or analyze another indicator?"
            )
        return (
            "API é uma interface que permite que sistemas conversem entre si por meio de regras, "
            "requisições e respostas bem definidas. Quer que eu conecte esse conceito ao fluxo de "
            "dados do Dashboard CTI ou prefere analisar outro indicador?"
        )

    termos = {
        "ebitda": ("EBITDA", "Margem EBITDA", "Receita Liquida"),
        "ncg": ("NCG",),
        "liquidez": ("Liquidez corrente",),
        "ciclo": ("Ciclo Financeiro",),
        "tesouraria": ("Saldo de Tesouraria",),
        "saldo": ("Saldo de Tesouraria", "Saldo final"),
        "dfc": ("DFC", "Geracao de Caixa", "Investimentos", "Saldo final"),
        "receita": ("Receita Liquida", "Receita"),
        "break": ("Ponto de equilibrio", "Margem de seguranca", "Margem de contribuicao"),
        "equilibrio": ("Ponto de equilibrio", "Margem de seguranca", "Margem de contribuicao"),
    }
    chaves = [v for termo, vals in termos.items() if termo in pergunta for v in vals]
    linhas = []
    for linha in extra_context.splitlines():
        limpo = linha.strip()
        if not limpo.startswith("- "):
            continue
        if not chaves or any(chave.lower() in limpo.lower() for chave in chaves):
            linhas.append(limpo)
        if len(linhas) >= 6:
            break

    if linhas:
        valores_extraidos = [linha.removeprefix("- ").rstrip(".") for linha in linhas[:4]]
        if len(valores_extraidos) == 1:
            valores = valores_extraidos[0]
        else:
            valores = ", ".join(valores_extraidos[:-1]) + f" e {valores_extraidos[-1]}"
        if "ebitda" in pergunta:
            return (
                "EBITDA é uma medida operacional que ajuda a enxergar a geração de resultado antes "
                f"dos efeitos financeiros, impostos, depreciação e amortização. Na base ativa do "
                f"Dashboard CTI, esse indicador aparece junto de {valores}, o que ajuda a conectar "
                f"a margem operacional ao desempenho do recorte atual. {fechamento}"
            )
        if "ncg" in pergunta:
            return (
                "NCG mostra a necessidade de capital de giro da operação, comparando ativos e "
                f"passivos operacionais. No recorte atual da base ativa, a leitura passa por {valores}, "
                "indicando quanto caixa operacional fica preso no ciclo do negócio. "
                f"{fechamento}"
            )
        if "liquidez" in pergunta:
            return (
                "Liquidez corrente indica a capacidade de cobrir obrigações de curto prazo com "
                f"ativos circulantes. No recorte atual da base ativa, o dado se conecta a {valores}, "
                "então a leitura deve considerar tanto solvência quanto pressão de caixa. "
                f"{fechamento}"
            )
        intro = "Na base ativa do Dashboard CTI, o recorte atual indica" if lang != "en" else "In the active CTI dashboard dataset, the current slice shows"
        return f"{intro} {valores}. {fechamento}"
    if lang == "en":
        return "I can answer from the active CTI dashboard dataset when the question refers to project indicators, DRE, BP, DFC, scenarios, or dashboard navigation. Would you like me to open a related dashboard tab or analyze a specific indicator?"
    return "Posso responder com base na base ativa do Dashboard CTI quando a pergunta envolver indicadores, DRE, BP, DFC, cenários ou navegação do painel. Quer que eu abra uma aba relacionada ou analise um indicador específico?"


@dataclass
class RagEngine:
    documents: list[Document]
    embeddings: TfidfEmbeddings
    vectors: np.ndarray
    backend: str
    _index: object | None = field(default=None, repr=False)

    @classmethod
    def from_ranking(cls, ranking: pd.DataFrame) -> "RagEngine":
        docs = docs_cenarios(ranking) + docs_glossario() + docs_manuais()
        if not docs:
            docs = [Document(page_content="Base CTI sem documentos.", metadata={"source": "vazio"})]
        texts = [d.page_content for d in docs]
        emb = TfidfEmbeddings()
        emb.fit(texts)
        vectors = np.asarray(emb.embed_documents(texts), dtype=np.float32)
        backend = "numpy"
        index = None
        try:
            index = faiss_index(vectors)
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
            ((prioridade_fonte(self.documents[i], score), i) for score, i in pares),
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
            return _resposta_sem_llm(question, extra_context, lang), fontes
        resposta = gerar_llm(question, contexto, lang, history, chave)
        return resposta, fontes
