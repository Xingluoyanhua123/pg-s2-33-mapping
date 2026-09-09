import logging
import os
from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware

from .models import Course, CourseMapping, MappingCreate, VoiceCommand, VoiceCommandResult
from .repository import CourseRepository, MappingRepository
from .service import MappingService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("credit-mapping.main")

app = FastAPI(
    title="Voice Credit Mapping Prototype API",
    version="0.2.0",
    description="Voice-interactive prototype for credit mapping.",
)

frontend_origin = os.getenv("FRONTEND_ORIGIN", "").rstrip("/")

allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

if frontend_origin:
    allowed_origins.append(frontend_origin)


app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

course_repository = CourseRepository()
mapping_repository = MappingRepository()
service = MappingService(course_repository, mapping_repository)


@app.get("/")
def root():
    return {"name": "Voice Credit Mapping Prototype", "version": "0.2.0", "status": "running", "docs": "/docs"}


@app.get("/api/courses", response_model=list[Course])
def get_courses():
    return service.list_courses()


@app.get("/api/mappings", response_model=list[CourseMapping])
def get_mappings():
    return service.list_mappings()


@app.post("/api/mappings", response_model=CourseMapping, status_code=status.HTTP_201_CREATED)
def create_mapping(request: MappingCreate):
    return service.create_mapping(request)


@app.delete("/api/mappings/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_mapping(mapping_id: int):
    service.delete_mapping(mapping_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/api/voice-command", response_model=VoiceCommandResult)
def voice_command(command: VoiceCommand):
    return service.interpret_voice_command(command.text, command.session_id)
