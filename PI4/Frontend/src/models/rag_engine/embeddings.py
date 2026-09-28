"""Embeddings locais baseados em TF-IDF."""

from __future__ import annotations

import numpy as np
from langchain_core.embeddings import Embeddings
from sklearn.feature_extraction.text import TfidfVectorizer


class TfidfEmbeddings(Embeddings):
    """Embeddings locais (TF-IDF) para o FAISS, sem depender de API para retrieval."""

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
