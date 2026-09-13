import math
from typing import List, Tuple, Dict
from app.services.interfaces import VectorStore


class InMemoryVectorStore(VectorStore):
    """
    Simple cosine-similarity search, no external DB required.
    Swap for pgvector/FAISS later without changing the calling code (see interfaces.py).
    """

    def __init__(self):
        self._items: Dict[str, Tuple[str, List[float], dict]] = {}

    def add(self, item_id: str, text: str, vector: List[float], metadata: dict) -> None:
        self._items[item_id] = (text, vector, metadata)

    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def search(self, query_vector: List[float], top_k: int = 3) -> List[Tuple[str, float, dict]]:
        scored = [
            (item_id, self._cosine_similarity(query_vector, vector), metadata)
            for item_id, (text, vector, metadata) in self._items.items()
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]
