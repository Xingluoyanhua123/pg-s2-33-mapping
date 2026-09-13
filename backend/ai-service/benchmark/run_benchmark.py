"""
Benchmarks each model in MODEL_REGISTRY against the multi-source fake dataset.
Measures: precision@1, recall@1, average latency, and memory consumption.

Run: PYTHONPATH=. python3 benchmark/run_benchmark.py
"""
import json
import time
import tracemalloc
from pathlib import Path

import psutil

from benchmark.data_loader import load_all_sources
from benchmark.model_registry import MODEL_REGISTRY

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.embedding_provider import MockEmbeddingProvider, HuggingFaceEmbeddingProvider
from app.services.llm_provider import MockLLMProvider, HuggingFaceLLMProvider
from app.services.vector_store import InMemoryVectorStore
from app.services.mapping_service import CreditMappingOrchestrator

OUTPUT_PATH = Path(__file__).parent / "benchmark_results.json"


def get_process_memory_mb() -> float:
    process = psutil.Process()
    return process.memory_info().rss / (1024 * 1024)


def benchmark_model(model_config: dict, eval_records: list) -> dict:
    """Runs one model through the full pipeline and computes real metrics."""
    print(f"\n--- Benchmarking {model_config['display_name']} ({model_config['mode']} mode) ---")

    mem_before = get_process_memory_mb()
    tracemalloc.start()

    # Provider selection: mock (works everywhere) vs huggingface (needs network + real weights)
    if model_config["mode"] == "huggingface":
        embedding_provider = HuggingFaceEmbeddingProvider("sentence-transformers/all-MiniLM-L6-v2")
        llm_provider = HuggingFaceLLMProvider(model_config["hf_repo"])
    else:
        embedding_provider = MockEmbeddingProvider()
        llm_provider = MockLLMProvider()

    vector_store = InMemoryVectorStore()
    orchestrator = CreditMappingOrchestrator(embedding_provider, llm_provider, vector_store)

    mem_after_load = get_process_memory_mb()

    correct = 0
    total = len(eval_records)
    latencies = []

    for record in eval_records:
        start = time.time()
        result = orchestrator.run(record)
        latencies.append(time.time() - start)

        predicted = result.get("top_match", {}).get("course_code")
        if predicted == record["expected_mapping"]:
            correct += 1

    peak_mem = tracemalloc.get_traced_memory()[1] / (1024 * 1024)
    tracemalloc.stop()
    mem_after_inference = get_process_memory_mb()

    precision_at_1 = correct / total if total else 0.0
    recall_at_1 = correct / total if total else 0.0  # single-label task: precision == recall @1

    return {
        "model_id": model_config["id"],
        "display_name": model_config["display_name"],
        "hf_repo": model_config["hf_repo"],
        "mode": model_config["mode"],
        "params_billion": model_config["params_billion"],
        "precision_at_1": round(precision_at_1, 3),
        "recall_at_1": round(recall_at_1, 3),
        "correct": correct,
        "total": total,
        "avg_latency_ms": round(sum(latencies) / len(latencies) * 1000, 1) if latencies else 0,
        "process_rss_before_mb": round(mem_before, 1),
        "process_rss_after_load_mb": round(mem_after_load, 1),
        "process_rss_after_inference_mb": round(mem_after_inference, 1),
        "model_load_memory_delta_mb": round(mem_after_load - mem_before, 1),
        "python_peak_traced_memory_mb": round(peak_mem, 1),
    }


def main():
    eval_records = load_all_sources()
    print(f"Loaded {len(eval_records)} evaluation records from 3 source formats (JSON, CSV, XML)")

    results = [benchmark_model(model, eval_records) for model in MODEL_REGISTRY]

    report = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "eval_set_size": len(eval_records),
        "eval_sources": ["institution_a.json", "institution_b.csv", "institution_c.xml"],
        "results": results,
    }

    OUTPUT_PATH.write_text(json.dumps(report, indent=2))
    print(f"\nBenchmark complete. Results written to {OUTPUT_PATH}")

    print("\n=== Summary ===")
    for r in results:
        note = "" if r["mode"] == "huggingface" else "  (mock — swap to huggingface + rerun for real numbers)"
        print(f"{r['display_name']:30s} precision={r['precision_at_1']:.2f}  "
              f"latency={r['avg_latency_ms']}ms  mem_delta={r['model_load_memory_delta_mb']}MB{note}")


if __name__ == "__main__":
    main()
