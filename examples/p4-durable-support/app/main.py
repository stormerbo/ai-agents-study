"""Run with uvicorn app.main:app, loopback only for public demo tokens."""
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import psycopg

from .api import router
from .config import Settings
from .db import connect
from .models import ErrorResponse


def create_app(settings: Settings | None = None):
    application = FastAPI(title="Synthetic durable support", version="0.1.0")
    application.state.settings = settings or Settings.from_env()

    @application.exception_handler(HTTPException)
    async def http_error(request: Request, error: HTTPException):
        detail = error.detail if isinstance(error.detail, dict) else {"code": "http_error", "message": str(error.detail)}
        return JSONResponse(status_code=error.status_code, content={"error": detail}, headers=error.headers)

    @application.exception_handler(RequestValidationError)
    async def validation_error(request: Request, error: RequestValidationError):
        # FastAPI's default error includes invalid user inputs; omit them.
        return JSONResponse(status_code=422, content={"error": {"code": "validation_error", "message": "Invalid request fields, cursor or idempotency key"}})

    @application.exception_handler(psycopg.Error)
    async def database_error(request: Request, error: psycopg.Error):
        # Do not return exception strings, SQL values or DSNs.
        return JSONResponse(status_code=503, content={"error": {"code": "database_unavailable", "message": "Database unavailable"}})

    @application.get("/health/live")
    def live():
        return {"status": "live"}

    @application.get("/health/ready", responses={503: {"model": ErrorResponse}})
    def ready():
        with connect(application.state.settings.database_url) as conn:
            # A connected but unmigrated database is not ready.
            required = {"0001_base.sql", "0002_execution.sql", "0003_delivery.sql", "0004_manual_resolution.sql"}
            applied = {row["version"] for row in conn.execute("SELECT version FROM schema_migrations").fetchall()}
            if not required.issubset(applied):
                raise HTTPException(503, detail={"code": "schema_unavailable", "message": "Required migration missing"})
        return {"status": "ready"}

    application.include_router(router)
    return application


app = create_app()
