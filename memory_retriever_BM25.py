from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Sequence

import jieba
from rank_bm25 import BM25Okapi


TOKEN_PATTERN = re.compile(r"[a-z0-9_]+|[\u4e00-\u9fff]+")
EMPTY_DOCUMENT_TOKEN = "__empty_document__"


def tokenize_for_bm25(text: str):
    """
    Tokenize mixed Chinese & English
    返回结果list
    """
    tokens: list[str] = []
    for segment in TOKEN_PATTERN.findall(str(text).lower()):
        if "\u4e00" <= segment[0] <= "\u9fff":
            tokens.extend(token.strip() for token in jieba.lcut(segment, cut_all=False) if token.strip())
        else:
            tokens.append(segment)
    return tokens


@dataclass(frozen=True)
class BM25SearchResult:
    document_index: int
    score: float


class BM25MemoryRetriever:
    """
    Ranked memory documents through BM25.
    """

    def __init__(self, documents: Sequence[str], k1: float = 1.5, b: float = 0.75):
        """
        Input:
            documents: Sequence[str], 
            k1: 默认为1.5, 
            b: 默认为0.75
        """
        tokenized_documents = [tokenize_for_bm25(document) for document in documents]
        self._corpus = [tokens or [EMPTY_DOCUMENT_TOKEN] for tokens in tokenized_documents]
        self._model = BM25Okapi(self._corpus, k1=k1, b=b) if self._corpus else None

    def search(self, query, top_k):
        """
        Return the highest-scoring documents
        Latest documents win when score ties
        Input:
            query, 
            top_k: 默认返回top3
        """
        query_tokens = tokenize_for_bm25(query)
        if self._model is None or not query_tokens or top_k <= 0:
            return []

        scores = self._model.get_scores(query_tokens)
        ranked = sorted(
            enumerate(scores),
            key=lambda item: (float(item[1]), item[0]),
            reverse=True,
        )
        return [
            BM25SearchResult(document_index=index, score=float(score))
            for index, score in ranked[:top_k]
        ]
