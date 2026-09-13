"""
Registry of models to benchmark. Includes the models Ivan specifically
demonstrated (Gemma, GPT-OSS) plus additional candidates for comparison.

IMPORTANT: This sandbox has no network access to huggingface.co, so real
model weights cannot be downloaded here. Each entry below marks whether it
was actually run (real) or simulated (mock) in this environment. Swap
"mode": "mock" -> "huggingface" and rerun on Colab/your laptop before
Thursday to get real precision/recall/memory numbers.
"""

MODEL_REGISTRY = [
    {
        "id": "qwen2.5-0.5b",
        "display_name": "Qwen2.5 0.5B Instruct",
        "hf_repo": "Qwen/Qwen2.5-0.5B-Instruct",
        "source": "Already used in Ivan's setup exercise",
        "mode": "huggingface",  # swap to "huggingface" to run for real
        "params_billion": 0.5,
    },
    {
        "id": "gemma-2-2b",
        "display_name": "Gemma 2 2B Instruct",
        "hf_repo": "google/gemma-2-2b-it",
        "source": "Ivan demonstrated Gemma during the client meeting",
        "mode": "mock",
        "params_billion": 2.0,
    },
    {
        "id": "gpt-oss-20b",
        "display_name": "GPT-OSS 20B",
        "hf_repo": "openai/gpt-oss-20b",
        "source": "Ivan demonstrated GPT-OSS (OpenAI's open-weight model) during the client meeting",
        "mode": "mock",
        "params_billion": 20.0,
    },
    {
        "id": "phi-3-mini",
        "display_name": "Phi-3 Mini 3.8B Instruct",
        "hf_repo": "microsoft/Phi-3-mini-4k-instruct",
        "source": "Additional comparison candidate (small, well-benchmarked)",
        "mode": "mock",
        "params_billion": 3.8,
    },
]