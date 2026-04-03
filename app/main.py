from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.documents import router as documents_router
from app.api.health import router as health_router
from app.api.kb import router as kb_router
from app.api.matrix import router as matrix_router
from app.api.outputs import router as outputs_router
from app.api.pipeline import router as pipeline_router
from app.api.pipeline_stages import router as pipeline_stages_router
from app.api.sync import router as sync_router
from app.api.tasks import router as tasks_router
from app.core.config import settings


@asynccontextmanager
async def lifespan(application: FastAPI):
    if settings.sentry_dsn:
        import sentry_sdk
        sentry_sdk.init(dsn=settings.sentry_dsn)
    yield


app = FastAPI(
    title="CR Intelligence Platform",
    description=(
        "Knowledge-compilation platform for official clinical guidelines: source vault, normalized corpus, "
        "compiled knowledge base, evidence layer, and analytic outputs. INN substitution matrix is a "
        "downstream, explainable product artifact built on that stack."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(documents_router)
app.include_router(sync_router)
app.include_router(kb_router)
app.include_router(outputs_router)
app.include_router(matrix_router)
app.include_router(tasks_router)
app.include_router(pipeline_router)
app.include_router(pipeline_stages_router)


@app.get("/")
async def root():
    return {
        "service": "CR Intelligence Platform",
        "version": "0.1.0",
        "pipeline_storage_stages": "/pipeline/storage-stages",
        "storage_stages_doc": "docs/STORAGE_STAGES.md",
    }
