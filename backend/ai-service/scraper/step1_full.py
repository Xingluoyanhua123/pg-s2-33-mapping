import requests
import json
import time

API_URL = 'https://uosa-search.funnelback.squiz.cloud/s/search.html'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json',
    'Referer': 'https://adelaide.edu.au/'
}

def fetch_page(query, start_rank):
    params = {
        'collection': 'uosa~sp-aem-prod',
        'profile': 'site-search',
        'f.Tabs|type': 'Degrees & Courses',
        'query': query,
        'start_rank': start_rank,
        'form': 'json',
        'num_ranks': 50
    }
    resp = requests.get(API_URL, params=params, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    return resp.json()

def discover_degree_urls(query='*', max_pages=250):
    degree_urls = set()
    start_rank = 1
    last_log = time.time()

    for page_num in range(max_pages):
        try:
            data = fetch_page(query, start_rank)
        except Exception as e:
            print(f"ERROR on page {page_num+1}: {e}, retrying once...")
            time.sleep(2)
            data = fetch_page(query, start_rank)

        rp = data['response']['resultPacket']
        results = rp.get('results', [])

        if not results:
            print(f"No more results at start_rank={start_rank}. Stopping.")
            break

        for r in results:
            url = r.get('liveUrl', '')
            if '/study/degrees/' in url:
                degree_urls.add(url)

        summary = rp['resultsSummary']
        print(f"Page {page_num+1}: start_rank={start_rank}/{summary['totalMatching']}, degree_urls_so_far={len(degree_urls)}")

        if time.time() - last_log > 45:
            print(f"[HEARTBEAT] Still running after {page_num+1} pages, {len(degree_urls)} degree URLs so far")
            last_log = time.time()

        next_start = summary.get('nextStart')
        if not next_start:
            print("Reached last page.")
            break
        start_rank = next_start
        time.sleep(0.5)

    return degree_urls

if __name__ == '__main__':
    urls = discover_degree_urls(query='*', max_pages=250)
    with open('degrees.json', 'w') as f:
        json.dump(sorted(urls), f, indent=2)
    print(f"\nDONE. Found {len(urls)} unique degree URLs total. Saved to degrees.json")
