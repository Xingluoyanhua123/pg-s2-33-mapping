import logging
from .data import COURSES
from .models import Course, CourseMapping

logger = logging.getLogger("credit-mapping.repository")


class CourseRepository:
    def list_courses(self) -> list[Course]:
        logger.info("Reading available courses")
        return COURSES

    def get_course(self, course_id: int) -> Course | None:
        logger.info("Looking for course id=%s", course_id)
        return next((course for course in COURSES if course.id == course_id), None)

    def find_by_text(self, text: str) -> Course | None:
        cleaned = text.lower().strip()

        for course in COURSES:
            if course.code.lower() in cleaned:
                return course

        for course in COURSES:
            if course.name.lower() in cleaned:
                return course

        keywords = {
            "math": 1,
            "mathematics": 1,
            "information technology": 2,
            "it course": 2,
            "database": 3,
            "programming": 4,
        }
        for keyword, course_id in keywords.items():
            if keyword in cleaned:
                return self.get_course(course_id)

        return None


class MappingRepository:
    def __init__(self) -> None:
        self._mappings: list[CourseMapping] = []
        self._next_id = 1

    def list_mappings(self) -> list[CourseMapping]:
        logger.info("Reading %s mappings", len(self._mappings))
        return list(self._mappings)

    def find_by_source_course(self, course_id: int) -> CourseMapping | None:
        return next(
            (m for m in self._mappings if m.source_course_id == course_id),
            None,
        )

    def create(self, mapping: CourseMapping) -> CourseMapping:
        existing = self.find_by_source_course(mapping.source_course_id)
        if existing:
            return existing

        mapping.id = self._next_id
        self._next_id += 1
        self._mappings.append(mapping)
        logger.info(
            "Created mapping id=%s source=%s target=%s",
            mapping.id,
            mapping.source_course_code,
            mapping.target_course_code,
        )
        return mapping

    def delete(self, mapping_id: int) -> bool:
        before = len(self._mappings)
        self._mappings = [m for m in self._mappings if m.id != mapping_id]
        deleted = len(self._mappings) < before
        logger.info("Delete mapping id=%s result=%s", mapping_id, deleted)
        return deleted
