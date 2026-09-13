import requests
import json
import time
import re
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html',
    'Referer': 'https://adelaide.edu.au/'
}

def extract_courses_from_degree_page(url):
    """Finds every course link on a degree page and pulls code/name/units from it."""
    resp = requests.get(url, headers=HEADERS, timeout=20)
    if resp.status_code != 200:
        return [], resp.status_code

    soup = BeautifulSoup(resp.text, 'html.parser')
    courses = []
    seen = set()

    for a in soup.find_all('a', href=True):
        href = a['href']
        if '/study/courses/' in href:
            text = a.get_text(strip=True)
            # Expected text pattern: "Course Name (6 units)" with course code often nearby
            match = re.search(r'\((\d+)\s*units?\)', text)
            units = match.group(1) if match else None
            name = re.sub(r'\s*\(\d+\s*units?\)', '', text).strip()

            # Try to extract course code from the URL itself, e.g. /comp-5004/
            code_match = re.search(r'/([a-z]+)-(\d{4})/?$', href)
            code = f"{code_match.group(1).upper()}{code_match.group(2)}" if code_match else None

            full_url = href if href.startswith('http') else f"https://adelaide.edu.au{href}"

            key = (code, full_url)
            if key in seen or not name:
                continue
            seen.add(key)

            courses.append({
                'course_code': code,
                'course_name': name,
                'units': units,
                'url': full_url
            })

    return courses, resp.status_code


def main():
    with open('degrees.json') as f:
        degree_urls = json.load(f)

    all_courses = {}  # keyed by url to dedupe across degrees
    degree_course_map = {}
    last_log = time.time()
    errors = []

    for i, degree_url in enumerate(degree_urls):
        try:
            courses, status = extract_courses_from_degree_page(degree_url)
        except Exception as e:
            print(f"ERROR fetching {degree_url}: {e}")
            errors.append(degree_url)
            continue

        degree_course_map[degree_url] = [c['url'] for c in courses]
        for c in courses:
            all_courses[c['url']] = c

        print(f"[{i+1}/{len(degree_urls)}] {degree_url} -> {len(courses)} courses (status {status})")

        if time.time() - last_log > 45:
            print(f"[HEARTBEAT] {i+1}/{len(degree_urls)} degrees processed, {len(all_courses)} unique courses so far")
            last_log = time.time()

        time.sleep(0.3)  # be polite

    with open('all_courses.json', 'w') as f:
        json.dump(list(all_courses.values()), f, indent=2)

    with open('degree_course_map.json', 'w') as f:
        json.dump(degree_course_map, f, indent=2)

    print(f"\nDONE. {len(all_courses)} unique courses found across {len(degree_urls)} degrees.")
    print(f"Errors on {len(errors)} degree pages (saved separately if needed).")

if __name__ == '__main__':
    main()
