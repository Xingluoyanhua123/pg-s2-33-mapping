import psycopg2

DB_CONFIG = {
    'host': 'localhost',
    'dbname': 'adelaide_uni_db',
    'user': 'postgres',
    'password': 'postgres'
}

def load_courses_from_db():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        SELECT course_code, title, overview
        FROM adelaide_uni_lectures
        WHERE overview IS NOT NULL AND overview != ''
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    courses = []
    for code, title, overview in rows:
        courses.append({
            'course_code': code,
            'course_title': title,
            'description': overview
        })
    return courses
