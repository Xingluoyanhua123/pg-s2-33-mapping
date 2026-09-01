from .models import Course

COURSES = [
    Course(
        id=1,
        code="MATH101",
        name="Mathematics I",
        units=6,
        suggested_target_code="MATH1001",
        suggested_target_name="Foundations of Mathematics",
    ),
    Course(
        id=2,
        code="IT101",
        name="Introduction to Information Technology",
        units=6,
        suggested_target_code="COMP1000",
        suggested_target_name="Introduction to Programming",
    ),
    Course(
        id=3,
        code="DB201",
        name="Database Systems",
        units=6,
        suggested_target_code="COMP2003",
        suggested_target_name="Database Systems",
    ),
    Course(
        id=4,
        code="CS105",
        name="Programming Fundamentals",
        units=6,
        suggested_target_code="COMP1002",
        suggested_target_name="Programming Fundamentals",
    ),
]
