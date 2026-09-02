from datetime import datetime
from pydantic import BaseModel, Field


class Course(BaseModel):
    id: int
    code: str
    name: str
    units: int
    description: str = ""
    learning_outcomes: str = ""
    suggested_target_code: str = ""
    suggested_target_name: str = ""


class MappingCreate(BaseModel):
    source_course_id: int


class CourseMapping(BaseModel):
    id: int
    source_course_id: int
    source_course_code: str
    source_course_name: str
    target_course_code: str
    target_course_name: str
    decision: str = "Suggested"
    created_at: datetime = Field(default_factory=datetime.now)


class VoiceCommand(BaseModel):
    text: str
    session_id: str


class VoiceCommandResult(BaseModel):
    action: str
    message: str
    should_continue: bool = True
    mapping: CourseMapping | None = None
