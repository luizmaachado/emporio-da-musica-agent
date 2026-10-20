"""Fake embeddings: a bag of words, so texts that share words are close. No model, no network."""
import math
import zlib
from typing import override

from langchain_core.embeddings import Embeddings

from emporio.domain.text import normalize_text

_DIMENSIONS = 256


class WordEmbeddings(Embeddings):
    @override
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_query(text) for text in texts]

    @override
    def embed_query(self, text: str) -> list[float]:
        vector = [0.0] * _DIMENSIONS
        for word in normalize_text(text).split():
            vector[zlib.crc32(word.encode()) % _DIMENSIONS] += 1.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]
