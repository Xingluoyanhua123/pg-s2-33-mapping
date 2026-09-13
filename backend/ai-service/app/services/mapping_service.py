import logging
from app.data.db_catalog import load_courses_from_db

from app.services.interfaces import AgentOrchestrator, LLMProvider, RetrievalService

logger = logging.getLogger(__name__)


class CreditMappingOrchestrator(AgentOrchestrator):
    """
    Real data flow:
      1. Load the (fake) Adelaide course catalog and index it via RetrievalService.
      2. Retrieve the closest matching Adelaide course(s) for the student's prior course.
      3. Ask the LLM to generate a justification for the top match.
      4. Return a structured mapping decision with confidence + explanation.

    Depends only on RetrievalService and LLMProvider - not on embedding/vector-store
    internals directly - so the retrieval strategy can be swapped independently.
    """

    def __init__(self, retrieval_service: RetrievalService, llm_provider: LLMProvider):
        self.retrieval_service = retrieval_service
        self.llm_provider = llm_provider
        self._index_catalog()

    def _index_catalog(self) -> None:
        catalog = load_courses_from_db()
        logger.info(f"Loaded {len(catalog)} real courses from PostgreSQL")
        for course in catalog:
            text = f"{course['course_title']}: {course['description']}"
            self.retrieval_service.index(item_id=course["course_code"], text=text, metadata=course)
        logger.info(f"Indexed {len(catalog)} catalog courses via retrieval service")

    def run(self, student_record: dict) -> dict:
        prior_course_text = (
            f"{student_record['prior_course_title']}: {student_record['prior_course_description']}"
        )
        logger.info(f"Mapping request for: {student_record['prior_course_title']}")

        matches = self.retrieval_service.retrieve(prior_course_text, top_k=3)

        if not matches:
            return {"status": "no_match", "candidates": []}

        top_id, top_score, top_meta = matches[0]

        prompt = (
            f"A student previously completed a course titled '{student_record['prior_course_title']}' "
            f"described as: {student_record['prior_course_description']}\n\n"
            f"We are considering mapping it to the Adelaide course '{top_meta['course_title']}' "
            f"({top_meta['course_code']}), described as: {top_meta['description']}\n\n"
            "In 2-3 sentences, explain whether this is a reasonable credit mapping and why."
        )
        explanation = self.llm_provider.generate(prompt)

        return {
            "status": "match_found",
            "top_match": {
                "course_code": top_meta["course_code"],
                "course_title": top_meta["course_title"],
                "similarity_score": round(top_score, 4),
            },
            "explanation": explanation,
            "other_candidates": [
                {
                    "course_code": meta["course_code"],
                    "course_title": meta["course_title"],
                    "similarity_score": round(score, 4),
                }
                for _, score, meta in matches[1:]
            ],
        }
