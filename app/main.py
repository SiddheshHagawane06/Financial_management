import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.api.v1.router import api_router

settings = get_settings()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    description="Financial Document Management with Semantic RAG Analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    """Auto-create all tables on startup (safe if already exist)."""
    try:
        from app.db.session import engine, Base
        import app.models.user  # noqa – registers all models
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables verified / created.")
    except Exception as e:
        logger.error(f"❌ DB startup error: {e}")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Return JSON with the real error message instead of a blank 500."""
    logger.exception(f"Unhandled error on {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )


app.include_router(api_router)


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "app": settings.APP_NAME}


@app.get("/db-check", tags=["Health"])
def db_check():
    """Quick diagnostic: confirms DB connection and lists tables."""
    try:
        from sqlalchemy import inspect
        from app.db.session import engine
        insp = inspect(engine)
        tables = insp.get_table_names()
        return {"status": "connected", "tables": tables}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
