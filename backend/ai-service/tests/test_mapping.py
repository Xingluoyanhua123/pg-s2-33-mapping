import os
os.environ["AI_LLM_PROVIDER"] = "mock"
os.environ["AI_EMBEDDING_PROVIDER"] = "mock"

from fastapi.testclient import TestClient
from app.main import app


def test_map_credit_returns_structured_decision():
    with TestClient(app) as client:
        payload = {
            "student_id": "S1234567",
            "prior_course_title": "Introduction to Python Programming",
            "prior_course_description": "Covers variables, loops, functions, and basic data structures.",
            "prior_institution": "University of Melbourne",
        }
        response = client.post("/api/v1/map-credit", json=payload)
        assert response.status_code == 200

        body = response.json()
        assert body["status"] == "match_found"
        assert "top_match" in body
        assert "course_code" in body["top_match"]
        assert "explanation" in body
        assert isinstance(body["other_candidates"], list)
