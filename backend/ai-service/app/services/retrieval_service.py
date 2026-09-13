import logging
from typing import List, Tuple

from app.services.interfaces import RetrievalService, EmbeddingProvider, VectorStore

logger = logging.getLogger(__name__)


class SemanticRetrievalService(RetrievalService):
    """
    Default retrieval implementation: embeds the query with an EmbeddingProvider,
    then searches a VectorStore for the closest matches. Kept as its own class
    (rather than inline in the orchestrator) so retrieval strategy can be swapped
    later - e.g. hybrid keyword+semantic search - without touching business logic.
    """

    def __init__(self, embedding_provider: EmbeddingProvider, vector_store: VectorStore):
        self.embedding_provider = embedding_provider
        self.vector_store = vector_store

    def index(self, item_id: str, text: str, metadata: dict) -> None:
        vector = self.embedding_provider.embed(text)
        self.vector_store.add(item_id=item_id, text=text, vector=vector, metadata=metadata)

    def retrieve(self, query_text: str, top_k: int = 3) -> List[Tuple[str, float, dict]]:
        query_vector = self.embedding_provider.embed(query_text)
        results = self.vector_store.search(query_vector, top_k=top_k)
        logger.info(f"Retrieval returned {len(results)} candidates for query")
        return results
