FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

EXPOSE 8000

# LLM/embedding provider default to "mock" so the container starts even without
# Hugging Face network access; override AI_LLM_PROVIDER / AI_EMBEDDING_PROVIDER
# to "huggingface" at runtime for real models.
ENV AI_LLM_PROVIDER=mock
ENV AI_EMBEDDING_PROVIDER=mock

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
