import requests
import json
import time
import re
import os
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html',
    'Referer': 'https://adelaide.edu.au/'
}

OUTPUT_FILE = 'course_details.json'

def get_field_after_heading(soup, heading_text):
    """Finds an <h2>/<h3> with given text, returns the text of the next sibling element."""
    heading = soup.find(lambda tag: tag.name in ['h2', 'h3'] and heading_text.lower() in tag.get_text(strip=True).lower())
    if not heading:
        return None
    nxt = heading.find_next_sibling()
    if nxt:
        text = nxt.get_text(separator=' ', strip=True)
        return text if text else None
    return None

def extract_course_detail(url):
    resp = requests.get(url, headers=HEADERS, timeout=20)
    if resp.status_code != 200:
        return None, resp.status_code

    soup = BeautifulSoup(resp.text, 'html.parser')

    title_tag = soup.find('h1')
    title = title_tag.get_text(strip=True) if title_tag else None

    overview = get_field_after_heading(soup, 'Course overview')
    outcomes_heading = soup.find(lambda tag: tag.name in ['h2','h3'] and 'learning outcomes' in tag.get_text(strip=True).lower())
    outcomes = []
    if outcomes_heading:
        ul = outcomes_heading.find_next('ul')
        if ul:
            outcomes = [li.get_text(strip=True) for li in ul.find_all('li')]

    prerequisites = get_field_after_heading(soup, 'Prerequisite')
    corequisites = get_field_after_heading(soup, 'Corequisite')
    antirequisites = get_field_after_heading(soup, 'Antirequisite')
    assumed_knowledge = get_field_after_heading(soup, 'Assumed knowledge')

    assessment_heading = soup.find(lambda tag: tag.name in ['h2','h3'] and 'assessment' in tag.get_text(strip=True).lower())
    assessment = []
    if assessment_heading:
        ul = assessment_heading.find_next('ul')
        if ul:
            assessment = [li.get_text(strip=True) for li in ul.find_all('li')]

    meta = {}
    for meta_tag in soup.find_all('meta'):
        key = meta_tag.get('name') or meta_tag.get('property') or ''
        if key in ('courseCode', 'unitValue', 'studyLevel', 'subjectArea'):
            meta[key] = meta_tag.get('content')

    return {
        'url': url,
        'title': title,
        'course_code': meta.get('courseCode'),
        'unit_value': meta.get('unitValue'),
        'study_level': meta.get('studyLevel'),
        'subject_area': meta.get('subjectArea'),
        'overview': overview,
        'learning_outcomes': outcomes,
        'prerequisites': prerequisites,
        'corequisites': corequisites,
        'antirequisites': antirequisites,
        'assumed_knowledge': assumed_knowledge,
        'assessment': assessment,
    }, resp.status_code


def main():
    with open('all_courses.json') as f:
        courses = json.load(f)

    # Resume support: load existing progress if present
    results = []
    done_urls = set()
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE) as f:
            results = json.load(f)
        done_urls = {r['url'] for r in results}
        print(f"Resuming: {len(done_urls)} already done, skipping those.")

    last_log = time.time()
    last_save = time.time()
    errors = []

    for i, course in enumerate(courses):
        url = course['url']
        if url in done_urls:
            continue

        try:
            detail, status = extract_course_detail(url)
            if detail:
                results.append(detail)
        except Exception as e:
            print(f"ERROR on {url}: {e}")
            errors.append(url)
            continue

        if (i + 1) % 25 == 0 or time.time() - last_log > 45:
            print(f"[{i+1}/{len(courses)}] processed. {len(results)} details collected so far.")
            last_log = time.time()

        # Save progress every 100 courses in case of interruption
        if time.time() - last_save > 60:
            with open(OUTPUT_FILE, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"[SAVED] Progress checkpoint written, {len(results)} records so far.")
            last_save = time.time()

        time.sleep(0.3)

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nDONE. {len(results)} course details saved to {OUTPUT_FILE}.")
    print(f"Errors on {len(errors)} courses.")
    if errors:
        with open('step3_errors.json', 'w') as f:
            json.dump(errors, f, indent=2)

if __name__ == '__main__':
    main()
