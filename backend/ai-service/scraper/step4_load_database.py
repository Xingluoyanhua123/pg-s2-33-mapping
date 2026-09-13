import json
import psycopg2

DB_CONFIG = {
    'host': 'localhost',
    'dbname': 'adelaide_uni_db',
    'user': 'postgres',
    'password': 'postgres'
}

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS adelaide_uni_lectures (
    id SERIAL PRIMARY KEY,
    course_code VARCHAR(20) UNIQUE,
    title TEXT,
    unit_value INTEGER,
    study_level VARCHAR(100),
    subject_area VARCHAR(200),
    overview TEXT,
    learning_outcomes TEXT[],
    prerequisites TEXT,
    corequisites TEXT,
    antirequisites TEXT,
    assumed_knowledge TEXT,
    assessment TEXT[],
    url TEXT
);
"""

CREATE_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_course_code ON adelaide_uni_lectures (course_code);
CREATE INDEX IF NOT EXISTS idx_subject_area ON adelaide_uni_lectures (subject_area);
CREATE INDEX IF NOT EXISTS idx_study_level ON adelaide_uni_lectures (study_level);
"""

INSERT_SQL = """
INSERT INTO adelaide_uni_lectures
(course_code, title, unit_value, study_level, subject_area, overview,
 learning_outcomes, prerequisites, corequisites, antirequisites, assumed_knowledge, assessment, url)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (course_code) DO UPDATE SET
    title = EXCLUDED.title,
    unit_value = EXCLUDED.unit_value,
    study_level = EXCLUDED.study_level,
    subject_area = EXCLUDED.subject_area,
    overview = EXCLUDED.overview,
    learning_outcomes = EXCLUDED.learning_outcomes,
    prerequisites = EXCLUDED.prerequisites,
    corequisites = EXCLUDED.corequisites,
    antirequisites = EXCLUDED.antirequisites,
    assumed_knowledge = EXCLUDED.assumed_knowledge,
    assessment = EXCLUDED.assessment,
    url = EXCLUDED.url;
"""

def safe_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

def main():
    with open('course_details.json') as f:
        courses = json.load(f)

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute(CREATE_TABLE_SQL)
    cur.execute(CREATE_INDEX_SQL)
    conn.commit()
    print("Table and indexes created.")

    inserted = 0
    skipped = 0

    for course in courses:
        code = course.get('course_code')
        if not code:
            skipped += 1
            continue

        cur.execute(INSERT_SQL, (
            code,
            course.get('title'),
            safe_int(course.get('unit_value')),
            course.get('study_level'),
            course.get('subject_area'),
            course.get('overview'),
            course.get('learning_outcomes') or [],
            course.get('prerequisites'),
            course.get('corequisites'),
            course.get('antirequisites'),
            course.get('assumed_knowledge'),
            course.get('assessment') or [],
            course.get('url'),
        ))
        inserted += 1

        if inserted % 500 == 0:
            conn.commit()
            print(f"Committed {inserted} records so far...")

    conn.commit()
    print(f"\nDONE. Inserted/updated {inserted} records. Skipped {skipped} (missing course_code).")

    cur.execute("SELECT COUNT(*) FROM adelaide_uni_lectures;")
    total = cur.fetchone()[0]
    print(f"Total rows now in adelaide_uni_lectures table: {total}")

    cur.close()
    conn.close()

if __name__ == '__main__':
    main()
