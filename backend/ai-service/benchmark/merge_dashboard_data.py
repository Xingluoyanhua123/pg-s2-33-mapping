"""
Merges real benchmark_results.json (models actually run) with simulated
numbers (models not yet downloaded) into one dashboard_data.json, tagging
each model as "measured" or "simulated" so the dashboard is always honest
about what's real.
"""
import json
import time
from pathlib import Path

BENCHMARK_RESULTS_PATH = Path(__file__).parent / "benchmark_results.json"
OUTPUT_PATH = Path(__file__).parent / "dashboard_data.json"

SIMULATED_FALLBACK = {
    "gemma-2-2b": {
        "display_name": "Gemma 2 2B Instruct",
        "hf_repo": "google/gemma-2-2b-it",
        "source_note": "Ivan demonstrated Gemma during the client meeting",
        "params_billion": 2.0,
        "precision_at_1": 0.78,
        "recall_at_1": 0.78,
        "avg_latency_ms": 420,
        "estimated_ram_gb": 4.5,
    },
    "gpt-oss-20b": {
        "display_name": "GPT-OSS 20B",
        "hf_repo": "openai/gpt-oss-20b",
        "source_note": "Ivan demonstrated GPT-OSS (OpenAI's open-weight model)",
        "params_billion": 20.0,
        "precision_at_1": 0.89,
        "recall_at_1": 0.89,
        "avg_latency_ms": 2100,
        "estimated_ram_gb": 40.0,
    },
    "phi-3-mini": {
        "display_name": "Phi-3 Mini 3.8B Instruct",
        "hf_repo": "microsoft/Phi-3-mini-4k-instruct",
        "source_note": "Additional comparison candidate",
        "params_billion": 3.8,
        "precision_at_1": 0.82,
        "recall_at_1": 0.82,
        "avg_latency_ms": 650,
        "estimated_ram_gb": 7.5,
    },
}

with open(BENCHMARK_RESULTS_PATH) as f:
    real_report = json.load(f)

merged_results = []

for r in real_report["results"]:
    if r["mode"] == "huggingface":
        merged_results.append({
            "model_id": r["model_id"],
            "display_name": r["display_name"],
            "hf_repo": r["hf_repo"],
            "source_note": "Actually run in this environment with real Hugging Face weights",
            "params_billion": r["params_billion"],
            "precision_at_1": r["precision_at_1"],
            "recall_at_1": r["recall_at_1"],
            "avg_latency_ms": r["avg_latency_ms"],
            "estimated_ram_gb": round(r["model_load_memory_delta_mb"] / 1024, 2),
            "data_source": "measured",
        })
    else:
        fallback = SIMULATED_FALLBACK.get(r["model_id"])
        if fallback:
            merged_results.append({
                "model_id": r["model_id"],
                **fallback,
                "data_source": "simulated",
            })

report = {
    "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    "status": "Mixed: Qwen2.5 numbers are REAL (measured). Gemma/GPT-OSS/Phi-3 are SIMULATED, pending a real run.",
    "eval_set_size": real_report["eval_set_size"],
    "eval_sources": ["institution_a.json (JSON)", "institution_b.csv (CSV)", "institution_c.xml (XML)"],
    "results": merged_results,
}

OUTPUT_PATH.write_text(json.dumps(report, indent=2))
print(f"Merged dashboard data written to {OUTPUT_PATH}")
for r in merged_results:
    print(f"  {r['display_name']}: {r['data_source']} — precision={r['precision_at_1']}")