import logging
from typing import List
from app.services.interfaces import EmbeddingProvider

logger = logging.getLogger(__name__)


class HuggingFaceEmbeddingProvider(EmbeddingProvider):
    """
    Uses sentence-transformers (a Hugging Face model) to embed text for
    semantic similarity search — the RAG-style retrieval half of the pipeline.
    """

    def __init__(self, model_name: str):
        from sentence_transformers import SentenceTransformer

        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        logger.info("Embedding model loaded successfully")

    def embed(self, text: str) -> List[float]:
        return self.model.encode(text, normalize_embeddings=True).tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return self.model.encode(texts, normalize_embeddings=True).tolist()


class MockEmbeddingProvider(EmbeddingProvider):
    """Deterministic fake embeddings — no network/model download required."""

    def _fake_vector(self, text: str) -> List[float]:
        import hashlib
        h = hashlib.sha256(text.lower().encode()).digest()
        return [b / 255.0 for b in h[:16]]

    def embed(self, text: str) -> List[float]:
        return self._fake_vector(text)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self._fake_vector(t) for t in texts]


def get_embedding_provider(provider_name: str, model_name: str) -> EmbeddingProvider:
    if provider_name == "huggingface":
        return HuggingFaceEmbeddingProvider(model_name)
    if provider_name == "mock":
        return MockEmbeddingProvider()
    raise ValueError(f"Unknown embedding provider: {provider_name}")
