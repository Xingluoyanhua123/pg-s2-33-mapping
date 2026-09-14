import json
import logging
import os
import re
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request as UrlRequest, urlopen

from fastapi import HTTPException

from .models import Course, CourseMapping, MappingCreate, VoiceCommandResult
from .repository import CourseRepository, MappingRepository

logger = logging.getLogger("credit-mapping.service")


@dataclass
class ConversationState:
    pending_course_id: int | None = None


class MappingService:
    def __init__(self, course_repository: CourseRepository, mapping_repository: MappingRepository) -> None:
        self.course_repository = course_repository
        self.mapping_repository = mapping_repository
        self.sessions: dict[str, ConversationState] = {}
        self.ollama_url = os.getenv(
            "OLLAMA_CHAT_URL",
            "http://127.0.0.1:11434/api/chat",
        )
        self.ollama_model = os.getenv(
            "OLLAMA_MODEL",
            "hermes3:8b",
        )

    def list_courses(self) -> list[Course]:
        return self.course_repository.list_courses()

    def list_mappings(self) -> list[CourseMapping]:
        return self.mapping_repository.list_mappings()

    def create_mapping(self, request: MappingCreate) -> CourseMapping:
        course = self.course_repository.get_course(request.source_course_id)
        if course is None:
            raise HTTPException(status_code=404, detail="Course not found")
        if course.suggested_target_code == "PENDING":
            raise HTTPException(
                status_code=400,
                detail=(
                    f"{course.code} does not have a reviewed target course yet. "
                    "AI analysis can provide a preliminary suggestion, "
                    "but university review is required."
                ),
            )

        existing = self.mapping_repository.find_by_source_course(course.id)
        if existing:
            return existing

        mapping = CourseMapping(
            id=0,
            source_course_id=course.id,
            source_course_code=course.code,
            source_course_name=course.name,
            target_course_code=course.suggested_target_code,
            target_course_name=course.suggested_target_name,
            decision="Suggested",
        )
        return self.mapping_repository.create(mapping)

    def delete_mapping(self, mapping_id: int) -> None:
        if not self.mapping_repository.delete(mapping_id):
            raise HTTPException(status_code=404, detail="Mapping not found")

    def _state(self, session_id: str) -> ConversationState:
        if session_id not in self.sessions:
            self.sessions[session_id] = ConversationState()
        return self.sessions[session_id]

    def ask_hermes(self, text: str) -> VoiceCommandResult:
        courses = self.list_courses()
        mappings = self.list_mappings()

        stop_words = {
            "the",
            "and",
            "for",
            "with",
            "this",
            "that",
            "course",
            "courses",
            "what",
            "why",
            "how",
            "does",
            "can",
            "could",
            "would",
            "map",
            "mapping",
            "credit",
            "explain",
        }

        query_words = {
            word
            for word in re.findall(r"[a-zA-Z0-9]+", text.lower())
            if len(word) >= 3 and word not in stop_words
        }

        def relevance(course: Course) -> int:
            code = course.code.lower()
            name = course.name.lower()

            searchable_text = " ".join(
                [
                    course.code,
                    course.name,
                    course.description,
                    course.learning_outcomes,
                ]
            ).lower()

            score = 0

            for word in query_words:
                if word in code:
                    score += 5
                elif word in name:
                    score += 3
                elif word in searchable_text:
                    score += 1

            return score

        ranked_courses = sorted(
            (
                (relevance(course), course)
                for course in courses
            ),
            key=lambda item: item[0],
            reverse=True,
        )

        relevant_courses = [
            course
            for score, course in ranked_courses
            if score > 0
        ][:3]

        catalogue = "\n".join(
            (
                f"- {course.code}: {course.name}; "
                f"candidate target: "
                f"{course.suggested_target_code}, "
                f"{course.suggested_target_name}"
            )
            for course in courses
        )

        if relevant_courses:
            relevant_context = "\n\n".join(
                (
                    f"Source course code: {course.code}\n"
                    f"Source course title: {course.name}\n"
                    f"Units: {course.units}\n"
                    f"Description: {course.description}\n"
                    f"Learning outcomes: {course.learning_outcomes}\n"
                    f"Candidate target: "
                    f"{course.suggested_target_code}, "
                    f"{course.suggested_target_name}"
                )
                for course in relevant_courses
            )
        else:
            relevant_context = (
                "No specific course record was identified from the question."
            )

        if mappings:
            mapping_context = "\n".join(
                (
                    f"- {mapping.source_course_code} is mapped to "
                    f"{mapping.target_course_code}"
                )
                for mapping in mappings
            )
        else:
            mapping_context = "No mappings have been confirmed yet."

        system_prompt = f"""
You are a course credit mapping assistant for a university prototype.

Available external course catalogue:
{catalogue}

Most relevant records retrieved from the uploaded spreadsheet:
{relevant_context}

Current confirmed prototype mappings:
{mapping_context}

Rules:
1. Use the retrieved spreadsheet information for course-specific answers.
2. Do not invent course codes, learning outcomes, or official decisions.
3. PENDING means that no target course has been reviewed.
4. For PENDING courses, you may analyse the course but must not claim
   that an official equivalence has been approved.
5. All suggested mappings require university review and approval.
6. If the necessary target-course information is unavailable, say so.
7. Keep the response concise and suitable for voice playback.
""".strip()

        payload = {
            "model": self.ollama_model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": text,
                },
            ],
            "stream": False,
            "options": {
                "temperature": 0.2,
            },
        }

        request = UrlRequest(
            self.ollama_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlopen(request, timeout=120) as response:
                result = json.loads(
                    response.read().decode("utf-8")
                )

            print(
                f"[MODEL CHECK] requested={self.ollama_model}, "
                f"returned={result.get('model', 'unknown')}",
                flush=True,
            )
            
            answer = (
                result.get("message", {})
                .get("content", "")
                .strip()
            )
            if not answer:
                raise ValueError("Ollama returned an empty answer")
            if "university review" not in answer.lower():
                answer += (
                    " Any final credit mapping must be reviewed "
                    "and approved by the university."
                )

            return VoiceCommandResult(
                action="ai_answer",
                message=answer,
            )

        except (
            HTTPError,
            URLError,
            TimeoutError,
            ValueError,
            json.JSONDecodeError,
        ) as error:
            logger.exception("Unable to call model %s: %s", self.ollama_model, error)

            return VoiceCommandResult(
                action="model_error",
                message=(
                    f"The local model {self.ollama_model} did not return a valid answer. "
                    "Please check that Ollama is running and try again."
                ),
            )   

    def interpret_voice_command(self, text: str, session_id: str) -> VoiceCommandResult:
        cleaned = text.lower().strip()
        state = self._state(session_id)
        logger.info("Voice command session=%s text=%s", session_id, text)

        if not cleaned:
            return VoiceCommandResult(action="none", message="I did not hear anything. Please try again.")

        yes_words = {"yes", "yeah", "yep", "sure", "okay", "ok", "confirm", "do it"}
        no_words = {"no", "nope", "cancel", "stop", "don't", "do not"}

        if state.pending_course_id is not None:
            if cleaned in yes_words:
                course = self.course_repository.get_course(state.pending_course_id)
                state.pending_course_id = None
                if course is None:
                    return VoiceCommandResult(action="error", message="I lost the selected course. Please try again.")

                mapping = self.create_mapping(MappingCreate(source_course_id=course.id))
                return VoiceCommandResult(
                    action="create_mapping",
                    message=(
                        f"Done. I added the mapping from {mapping.source_course_code} "
                        f"to {mapping.target_course_code}. Would you like to map another course?"
                    ),
                    mapping=mapping,
                )

            if cleaned in no_words:
                state.pending_course_id = None
                return VoiceCommandResult(
                    action="cancel",
                    message="No problem. I cancelled that mapping. What would you like to do next?",
                )

        if "help" in cleaned or "what can you do" in cleaned:
            return VoiceCommandResult(
                action="help",
                message=(
                    "You can ask me to map a course, list available courses, or show current mappings. "
                    "For example, say: Map Database Systems."
                ),
            )

        if "list courses" in cleaned or "show courses" in cleaned or "available courses" in cleaned:
            courses = self.list_courses()
            names = ", ".join(f"{c.code}, {c.name}" for c in courses)
            return VoiceCommandResult(action="list_courses", message=f"The available courses are: {names}.")

        if "show mappings" in cleaned or "list mappings" in cleaned or "current mappings" in cleaned:
            mappings = self.list_mappings()
            if not mappings:
                return VoiceCommandResult(action="list_mappings", message="There are no course mappings yet.")
            summary = "; ".join(f"{m.source_course_code} to {m.target_course_code}" for m in mappings)
            return VoiceCommandResult(action="list_mappings", message=f"The current mappings are: {summary}.")
        
        ai_question_markers = (
            "why",
            "explain",
            "compare",
            "difference",
            "how does",
            "what is",
            "recommend",
            "equivalent",
            "similar",
            "what are",
            "which",
        )

        if any(marker in cleaned for marker in ai_question_markers):
            return self.ask_hermes(text)


        course = self.course_repository.find_by_text(cleaned)
        mapping_words = ("add", "map", "mapping", "match", "credit", "recognise", "recognize", "transfer")

        if course and any(word in cleaned for word in mapping_words):
            if course.suggested_target_code == "PENDING":
                return VoiceCommandResult(
                    action="needs_review",
                    message=(
                        f"I found {course.code}, {course.name}, but it does not "
                        "have a reviewed target course yet. I can analyse its "
                        "description and learning outcomes, but the final mapping "
                        "requires university review and approval."
                    ),
                )
            existing = self.mapping_repository.find_by_source_course(course.id)
            if existing:
                return VoiceCommandResult(
                    action="already_exists",
                    message=(
                        f"{course.code}, {course.name}, is already mapped to "
                        f"{existing.target_course_code}, {existing.target_course_name}."
                    ),
                    mapping=existing,
                )

            state.pending_course_id = course.id
            return VoiceCommandResult(
                action="confirm_mapping",
                message=(
                    f"I found {course.code}, {course.name}. It can be mapped to "
                    f"{course.suggested_target_code}, {course.suggested_target_name}. "
                    f"Would you like me to add this mapping?"
                ),
            )

        if any(word in cleaned for word in mapping_words):
            return VoiceCommandResult(
                action="course_not_found",
                message=(
                    "I understood that you want to create a mapping, but I could not identify the course. "
                    "Please say the course code or course name."
                ),
            )

        return self.ask_hermes(text)