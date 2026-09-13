from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

router = APIRouter()


class StudentPriorCourse(BaseModel):
    student_id: str = Field(..., examples=["S1234567"])
    prior_course_title: str = Field(..., examples=["Intro to Computer Programming"])
    prior_course_description: str = Field(
        ..., examples=["Basic programming concepts using Java, loops, conditionals, and OOP basics."]
    )
    prior_institution: str = Field(..., examples=["University of Melbourne"])


@router.post("/map-credit")
def map_credit(payload: StudentPriorCourse, request: Request):
    """
    Real data flow: accepts an actual JSON request body (not a hardcoded example),
    runs it through embedding + retrieval + LLM explanation, and returns a structured decision.
    """
    orchestrator = request.app.state.orchestrator
    result = orchestrator.run(payload.model_dump())
    return {
        "student_id": payload.student_id,
        "prior_course_title": payload.prior_course_title,
        "prior_institution": payload.prior_institution,
        **result,
    }
