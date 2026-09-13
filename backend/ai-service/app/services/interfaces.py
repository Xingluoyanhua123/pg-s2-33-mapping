"""
Abstract interfaces so concrete providers (Hugging Face, Ollama, mock, etc.)
can be swapped without touching business logic (mapping_service.py).
"""
from abc import ABC, abstractmethod
from typing import List, Tuple


class LLMProvider(ABC):
    """Generates text (e.g. a natural-language justification for a mapping decision)."""

    @abstractmethod
    def generate(self, prompt: str, max_new_tokens: int = 120) -> str:
        ...


class EmbeddingProvider(ABC):
    """Turns text into a vector for semantic similarity search."""

    @abstractmethod
    def embed(self, text: str) -> List[float]:
        ...

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        ...


class VectorStore(ABC):
    """Stores (id, text, vector) tuples and supports nearest-neighbour search."""

    @abstractmethod
    def add(self, item_id: str, text: str, vector: List[float], metadata: dict) -> None:
        ...

    @abstractmethod
    def search(self, query_vector: List[float], top_k: int = 3) -> List[Tuple[str, float, dict]]:
        """Returns list of (item_id, similarity_score, metadata), best match first."""
        ...


class RetrievalService(ABC):
    """
    Orchestrates the retrieval step: turns a raw query string into a ranked list of
    matching catalogue items. Wraps EmbeddingProvider + VectorStore so the rest of
    the system depends on a single retrieval interface, not on embedding/vector-store
    internals directly. Swappable later for a different retrieval strategy (e.g.
    hybrid keyword+semantic search) without touching the orchestrator.
    """

    @abstractmethod
    def retrieve(self, query_text: str, top_k: int = 3) -> List[Tuple[str, float, dict]]:
        """Returns list of (item_id, similarity_score, metadata), best match first."""
        ...

    @abstractmethod
    def index(self, item_id: str, text: str, metadata: dict) -> None:
        """Embeds and adds one item to the underlying store."""
        ...


class AgentOrchestrator(ABC):
    """Coordinates retrieval + generation into a single mapping decision (placeholder for Hermes integration)."""

    @abstractmethod
    def run(self, student_record: dict) -> dict:
        ...
