"""
Environment-driven configuration for the standalone AI service.
Nothing here is hardcoded — swap providers/models via .env without touching code.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # -- Service --
    service_name: str = "credit-mapping-ai-service"
    service_port: int = 8000

    # -- LLM provider (generative explanation of a mapping decision) --
    llm_provider: str = "huggingface"          # huggingface | ollama | mock
    llm_model_name: str = "Qwen/Qwen2.5-0.5B-Instruct"

    # -- Embedding provider (semantic matching, RAG-style retrieval) --
    embedding_provider: str = "huggingface"     # huggingface | mock
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"

    # -- Vector store --
    vector_store: str = "in_memory"             # in_memory | pgvector | faiss (future)

    # -- Ollama (only used if llm_provider == "ollama", e.g. local dev) --
    ollama_base_url: str = "http://127.0.0.1:11434"

    class Config:
        env_file = ".env"
        env_prefix = "AI_"


settings = Settings()
