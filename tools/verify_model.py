"""Run real Ollama inference and save evidence; no third-party dependencies."""
import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

parser = argparse.ArgumentParser()
parser.add_argument('--model', default='gemma4:e2b')
parser.add_argument('--url', default='http://127.0.0.1:11434/api/chat')
parser.add_argument('--output', default='gemma-verification.json')
args = parser.parse_args()
prompt = ('Use only these synthetic test facts: Database Systems covers SQL, '
          'relational modelling and normalisation. No target course or credit '
          'approval is supplied. Summarise the learning outcomes and say whether '
          'a credit transfer can be confirmed. Do not invent an approval.')
record = {'timestamp_utc': datetime.now(timezone.utc).isoformat(),
          'requested_model': args.model, 'url': args.url, 'prompt': prompt,
          'status': 'failed', 'quality_review': 'Requires human review; this checks inference only.'}
started = time.perf_counter()
try:
    request = Request(args.url, data=json.dumps({'model': args.model,
        'messages': [{'role': 'user', 'content': prompt}], 'stream': False}).encode(),
        headers={'Content-Type': 'application/json'})
    with urlopen(request, timeout=300) as response:
        raw = json.load(response)
    record['raw_response'] = raw
    answer = raw.get('message', {}).get('content', '').strip()
    if not answer or not raw.get('done'):
        raise ValueError('No completed, non-empty answer received.')
    if raw.get('model') != args.model:
        raise ValueError('Returned model differs from requested model; inspect raw response.')
    record['status'] = 'inference_passed'
    print(answer)
except Exception as error:
    record['error'] = str(error)
    print(f'FAILED: {error}', file=sys.stderr)
record['elapsed_seconds'] = round(time.perf_counter() - started, 3)
Path(args.output).write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
print(f"Evidence saved: {args.output}")
sys.exit(0 if record['status'] == 'inference_passed' else 1)
