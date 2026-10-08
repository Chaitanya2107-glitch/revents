import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from starlette.exceptions import HTTPException

from app.config import get_settings
from app.database import get_engine
from app.schemas.common import ERROR_RESPONSES

logger = logging.getLogger("college_events")


class Health(BaseModel):
    status: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    logger.info(json.dumps({"event": "startup", "environment": settings.environment}))
    yield
    if get_engine.cache_info().currsize:
        get_engine().dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan,
                  responses=ERROR_RESPONSES)
    app.add_middleware(
        CORSMiddleware, allow_origins=settings.origins, allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
        expose_headers=["Content-Disposition"],
    )

    @app.middleware("http")
    async def response_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException):
        detail = exc.detail if isinstance(exc.detail, dict) else {
            "code": "HTTP_ERROR", "message": str(exc.detail)
        }
        return JSONResponse({"detail": detail}, status_code=exc.status_code, headers=exc.headers)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        errors = [{"loc": error["loc"], "message": error["msg"], "type": error["type"]}
                  for error in exc.errors()]
        return JSONResponse({"detail": {"code": "VALIDATION_ERROR", "message": "Invalid request.",
                                       "errors": errors}}, status_code=422)

    @app.exception_handler(SQLAlchemyError)
    async def database_error(request: Request, exc: SQLAlchemyError):
        if isinstance(exc, IntegrityError):
            status, code, message = 409, "DATA_CONFLICT", "This request conflicts with existing data."
        elif isinstance(exc, OperationalError):
            status, code, message = 503, "DATABASE_UNAVAILABLE", "Database temporarily unavailable."
        else:
            status, code, message = 500, "DATABASE_ERROR", "The request could not be completed."
        logger.error(json.dumps({"event": "database_error", "code": code}))
        return JSONResponse({"detail": {"code": code, "message": message}}, status_code=status)

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception):
        logger.error(json.dumps({"event": "internal_error", "error_type": type(exc).__name__}))
        return JSONResponse({"detail": {"code": "INTERNAL_ERROR", "message": "Unexpected server error."}},
                            status_code=500)

    @app.get("/api/health", response_model=Health, tags=["health"])
    def health():
        return {"status": "ok"}

    @app.get("/api/health/ready", response_model=Health, tags=["health"])
    def ready():
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ok"}

    from app.routers import auth, events, managers, notifications, registrations, students, tickets

    for router in (auth, students, events, registrations, tickets, managers, notifications):
        app.include_router(router.router)
    app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")
    return app


app = create_app()
