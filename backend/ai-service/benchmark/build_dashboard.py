import json
from pathlib import Path

DATA_PATH = Path(__file__).parent / "dashboard_data.json"
TEMPLATE_PATH = Path(__file__).parent / "dashboard_bootstrap_template.html"
OUTPUT_PATH = Path(__file__).parent / "dashboard.html"

with open(DATA_PATH) as f:
    data = json.load(f)

with open(TEMPLATE_PATH) as f:
    template = f.read()

final_html = template.replace("__DASHBOARD_DATA__", json.dumps(data))

OUTPUT_PATH.write_text(final_html)
print(f"Dashboard regenerated: {OUTPUT_PATH}")