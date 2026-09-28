"""Classe principal do motor RAG e retrieval."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd
from langchain_core.documents import Document

try:
    import faiss
except ImportError:
    faiss = None

from .answers import gerar_llm, resolve_api_key, resposta_extrativa
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
            return resposta_extrativa(question, hits, lang), fontes
        resposta = gerar_llm(question, contexto, lang, history, chave)
        return resposta, fontes
