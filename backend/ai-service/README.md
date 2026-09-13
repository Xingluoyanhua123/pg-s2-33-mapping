# Credit Mapping AI Service (SCRUM-27)

Standalone FastAPI service hosting local LLM + embedding + retrieval logic for the
Agentic AI Credit Mapping project. Runs independently of the main backend — no
shared auth/business persistence.

## What this demonstrates

A real, runnable HTTP service — not a notebook cell — with actual data flow:

1. A fake Adelaide course catalog (`app/data/fake_catalog.json`) is embedded and
   indexed into an in-memory vector store on startup.
2. `POST /api/v1/map-credit` accepts a real JSON request body describing a
   student's prior course.
3. The service embeds the input, retrieves the closest matching Adelaide
   course (RAG-style retrieval), and asks an LLM to generate a short
   explanation for the match (the agentic step).
4. Returns a structured JSON decision with the top match, similarity score,
   explanation, and other candidates.

## Providers

Two providers exist for both LLM and embeddings, swappable via `.env`:

| Provider | Requires | Use case |
|---|---|---|
| `mock` | Nothing | Local dev, CI, offline demos |
| `huggingface` | Network access to huggingface.co (downloads on first run) | Real inference |

Set in `.env`:
```
AI_LLM_PROVIDER=huggingface
AI_LLM_MODEL_NAME=Qwen/Qwen2.5-0.5B-Instruct
AI_EMBEDDING_PROVIDER=huggingface
AI_EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
```

> Note: real Hugging Face models must be downloaded in an environment with
> internet access to huggingface.co (e.g. Google Colab, your laptop, or
> Anna's server) — not every sandboxed environment allows this.

## Run locally

```bash
pip install -r requirements.txt
export AI_LLM_PROVIDER=huggingface
export AI_EMBEDDING_PROVIDER=huggingface
uvicorn app.main:app --reload
```

Then test it:
```bash
curl http://localhost:8000/api/v1/health

curl -X POST http://localhost:8000/api/v1/map-credit \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "S1234567",
    "prior_course_title": "Introduction to Python Programming",
    "prior_course_description": "Covers variables, loops, functions, and basic data structures.",
    "prior_institution": "University of Melbourne"
  }'
```

## Run with Docker

```bash
docker build -t credit-mapping-ai .
docker run -p 8000:8000 credit-mapping-ai
```
(Defaults to mock providers so it starts without Hugging Face network access —
override `AI_LLM_PROVIDER`/`AI_EMBEDDING_PROVIDER` env vars for real models.)

## Run tests

```bash
pytest tests/ -v
```

## Multi-model benchmark & dashboard (benchmark/)

Compares multiple models — including the ones Ivan demonstrated (Gemma,
GPT-OSS) plus additional candidates (Qwen2.5, Phi-3) — on precision@1,
recall@1, latency, and memory consumption.

- **`benchmark/data_loader.py`** — loads a fake, multi-source evaluation set:
  `institution_a.json`, `institution_b.csv`, `institution_c.xml`, normalizing
  three different export formats into one schema (real institutions won't all
  send clean JSON).
- **`benchmark/model_registry.py`** — the list of models to compare, each
  marked `mode: "mock"` or `"huggingface"`. Swap to `"huggingface"` per model
  to run for real.
- **`benchmark/run_benchmark.py`** — runs every registered model through the
  full pipeline against the eval set and measures **real** precision, recall,
  latency, and process memory (via `psutil`/`tracemalloc`). Run with:
  ```bash
  PYTHONPATH=. python3 benchmark/run_benchmark.py
  ```
  In mock mode (no Hugging Face access), precision comes out as 0% — this is
  expected and correct: mock embeddings are hash-based placeholders with no
  real semantic meaning, so the harness is proven to measure genuinely, not
  fake the output.
- **`benchmark/dashboard.html`** — a self-contained, no-dependency dashboard
  (open directly in a browser) showing precision, latency, and memory charts
  per model, plus a parameters table. **Currently populated with SIMULATED
  numbers** (`benchmark/generate_simulated_dashboard_data.py`), clearly
  labeled as such in the dashboard itself, since real weights can't be
  downloaded in this sandbox.

### Before Thursday

1. On Colab or a machine with Hugging Face access, edit
   `benchmark/model_registry.py` and set `"mode": "huggingface"` for each
   model you want real numbers for.
2. Run `PYTHONPATH=. python3 benchmark/run_benchmark.py` — this writes real
   metrics to `benchmark/benchmark_results.json`.
3. Adapt `generate_simulated_dashboard_data.py` (or write a small script) to
   read `benchmark_results.json` instead of hardcoded numbers, then
   regenerate `dashboard.html` the same way (`dashboard_template.html` +
   inject JSON).
4. GPT-OSS 20B in particular needs serious GPU memory — confirm it will
   actually run on whatever hardware you use before the meeting, or drop it
   from the comparison if it doesn't fit.

## What's real vs. placeholder right now

- **Real:** FastAPI app, endpoints, request/response flow, vector search logic,
  provider interfaces, logging with request IDs, tests, Docker build.
- **Fake (by design, per Ivan's instruction):** the course catalog — a stand-in
  until real Future Students team data arrives.
- **Not yet connected:** university database / real student records endpoint —
  this is the "real endpoint" gap raised in today's team discussion. Once Ivan
  provides a real data source or endpoint, it replaces `fake_catalog.json` and
  the input schema in `credit_mapping.py`.
