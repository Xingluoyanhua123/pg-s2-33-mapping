import logging, time, uuid
from fastapi import FastAPI, Request
from app.config import settings
from app.logging_config import setup_logging, request_id_ctx
from app.routers import health, credit_mapping
from app.services.llm_provider import get_llm_provider
from app.services.embedding_provider import get_embedding_provider
from app.services.vector_store import InMemoryVectorStore
from app.services.retrieval_service import SemanticRetrievalService
from app.services.mapping_service import CreditMappingOrchestrator

setup_logging()
logger = logging.getLogger(__name__)
app = FastAPI(title=settings.service_name)

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    req_id = str(uuid.uuid4())[:8]
    token = request_id_ctx.set(req_id)
    start = time.time()
    try:
        response = await call_next(request)
    finally:
        request_id_ctx.reset(token)
    duration_ms = round((time.time()-start)*1000, 1)
    logger.info(f"{request.method} {request.url.path} -> {duration_ms}ms")
    response.headers["X-Request-ID"] = req_id
    return response

@app.on_event("startup")
def startup():
    logger.info(f"Starting {settings.service_name} (llm={settings.llm_provider}/{settings.llm_model_name}, "
                f"embeddings={settings.embedding_provider}/{settings.embedding_model_name})")
    llm_provider = get_llm_provider(settings.llm_provider, settings.llm_model_name)
    embedding_provider = get_embedding_provider(settings.embedding_provider, settings.embedding_model_name)
    vector_store = InMemoryVectorStore()
    retrieval_service = SemanticRetrievalService(embedding_provider, vector_store)
    app.state.orchestrator = CreditMappingOrchestrator(retrieval_service=retrieval_service, llm_provider=llm_provider)
    logger.info("Startup complete - service ready to accept requests")

app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(credit_mapping.router, prefix="/api/v1", tags=["credit-mapping"])
