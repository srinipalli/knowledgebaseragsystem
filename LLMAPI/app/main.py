from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger

configure_logging()
settings = get_settings()
logger = get_logger(__name__)

app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router, prefix="/api")


@app.on_event("startup")
async def on_startup() -> None:
    logger.info(
        "api_startup_completed",
        app_name=settings.app_name,
        api_host=settings.api_host,
        api_port=settings.api_port,
        database_url=settings.database_url,
        embedding_model=settings.embedding_model,
        gemini_model=settings.gemini_model,
    )


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(
        "http_request_started",
        method=request.method,
        path=request.url.path,
        client=getattr(request.client, "host", "unknown"),
    )
    response = await call_next(request)
    logger.info(
        "http_request_completed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
    )
    return response
