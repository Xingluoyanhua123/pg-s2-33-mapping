import logging
from dataclasses import dataclass
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

    def list_courses(self) -> list[Course]:
        return self.course_repository.list_courses()

    def list_mappings(self) -> list[CourseMapping]:
        return self.mapping_repository.list_mappings()

    def create_mapping(self, request: MappingCreate) -> CourseMapping:
        course = self.course_repository.get_course(request.source_course_id)
        if course is None:
            raise HTTPException(status_code=404, detail="Course not found")

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

        course = self.course_repository.find_by_text(cleaned)
        mapping_words = ("add", "map", "mapping", "match", "credit", "recognise", "recognize", "transfer")

        if course and any(word in cleaned for word in mapping_words):
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

        return VoiceCommandResult(
            action="unknown",
            message="I am not sure what you mean yet. Try saying: Map MATH101, Show mappings, List courses, or Help.",
        )
