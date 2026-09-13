"""
Generates a SIMULATED benchmark report for dashboard demo purposes.

The real run_benchmark.py harness genuinely measures precision/recall/latency/
memory — but with the mock provider (no Hugging Face network access in this
sandbox), semantic matching is meaningless (hash-based fake vectors), so real
precision comes out as 0% across all models. That PROVES the harness works
correctly; it doesn't give a useful demo number.

This script instead produces realistic, clearly-labeled SIMULATED numbers
(following known real-world patterns: bigger models tend to score higher but
cost more latency/memory) so the dashboard has something meaningful to show
on Thursday. Replace by rerunning run_benchmark.py with
mode: "huggingface" on a machine with real Hugging Face access before
presenting these as real results.
"""
import json
import time
from pathlib import Path

OUTPUT_PATH = Path(__file__).parent / "dashboard_data.json"

# Illustrative only — NOT measured. Swap for real numbers before Thursday.
SIMULATED_RESULTS = [
    {
        "model_id": "qwen2.5-0.5b",
        "display_name": "Qwen2.5 0.5B Instruct",
        "hf_repo": "Qwen/Qwen2.5-0.5B-Instruct",
        "source_note": "Already used in Ivan's setup exercise",
        "params_billion": 0.5,
        "precision_at_1": 0.67,
        "recall_at_1": 0.67,
        "avg_latency_ms": 180,
        "estimated_ram_gb": 1.2,
    },
    {
        "model_id": "gemma-2-2b",
        "display_name": "Gemma 2 2B Instruct",
        "hf_repo": "google/gemma-2-2b-it",
        "source_note": "Ivan demonstrated Gemma during the client meeting",
        "params_billion": 2.0,
        "precision_at_1": 0.78,
        "recall_at_1": 0.78,
        "avg_latency_ms": 420,
        "estimated_ram_gb": 4.5,
    },
    {
        "model_id": "phi-3-mini",
        "display_name": "Phi-3 Mini 3.8B Instruct",
        "hf_repo": "microsoft/Phi-3-mini-4k-instruct",
        "source_note": "Additional comparison candidate",
        "params_billion": 3.8,
        "precision_at_1": 0.82,
        "recall_at_1": 0.82,
        "avg_latency_ms": 650,
        "estimated_ram_gb": 7.5,
    },
    {
        "model_id": "gpt-oss-20b",
        "display_name": "GPT-OSS 20B",
        "hf_repo": "openai/gpt-oss-20b",
        "source_note": "Ivan demonstrated GPT-OSS (OpenAI's open-weight model)",
        "params_billion": 20.0,
        "precision_at_1": 0.89,
        "recall_at_1": 0.89,
        "avg_latency_ms": 2100,
        "estimated_ram_gb": 40.0,
    },
]

report = {
    "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    "status": "SIMULATED — not measured. Replace with real run_benchmark.py output before Thursday.",
    "eval_set_size": 9,
    "eval_sources": ["institution_a.json (JSON)", "institution_b.csv (CSV)", "institution_c.xml (XML)"],
    "results": SIMULATED_RESULTS,
}

OUTPUT_PATH.write_text(json.dumps(report, indent=2))
print(f"Simulated dashboard data written to {OUTPUT_PATH}")
