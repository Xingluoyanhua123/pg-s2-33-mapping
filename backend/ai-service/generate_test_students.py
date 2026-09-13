"""
Generates 100 synthetic student records by sampling real courses from the
database. Each student's 'prior course' description is the REAL course
overview text, so we know exactly which course the AI SHOULD map to.
This gives genuine ground truth for measuring accuracy.
"""
import psycopg2
import json
import random

DB_CONFIG = {
    'host': 'localhost',
    'dbname': 'adelaide_uni_db',
    'user': 'postgres',
    'password': 'postgres'
}

def main():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        SELECT course_code, title, overview
        FROM adelaide_uni_lectures
        WHERE overview IS NOT NULL AND overview != ''
        ORDER BY RANDOM()
        LIMIT 100
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    students = []
    for i, (code, title, overview) in enumerate(rows):
        students.append({
            'student_id': f'S{1000000 + i}',
            'prior_course_title': title,
            'prior_course_description': overview,
            'prior_institution': 'Test University (synthetic)',
            'expected_course_code': code
        })

    with open('synthetic_students.json', 'w') as f:
        json.dump(students, f, indent=2)

    print(f"Generated {len(students)} synthetic student records -> synthetic_students.json")

if __name__ == '__main__':
    main()
