"""Request ID middleware and stable API error responses."""
from __future__ import annotations

import logging
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("quant.api")


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        request_id = getattr(request.state, "request_id", str(uuid4()))
        field_errors = [
            {"field": ".".join(str(part) for part in error["loc"]), "message": error["msg"]}
            for error in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content={
                "code": "validation_error",
                "message": "The request contains invalid fields.",
                "field_errors": field_errors,
                "request_id": request_id,
            },
        )

    @app.exception_handler(RuntimeError)
    async def runtime_error(request: Request, exc: RuntimeError):
        request_id = getattr(request.state, "request_id", str(uuid4()))
        logger.error("runtime_error request_id=%s error=%s", request_id, type(exc).__name__)
        return JSONResponse(
            status_code=503,
            content={
                "code": "dependency_unavailable",
                "message": str(exc),
                "field_errors": [],
                "request_id": request_id,
            },
        )

    @app.exception_handler(Exception)
    async def dependency_error(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", str(uuid4()))
        logger.exception("unhandled_dependency_error request_id=%s", request_id)
        return JSONResponse(
            status_code=503,
            content={
                "code": "dependency_unavailable",
                "message": "A required backend service is temporarily unavailable.",
                "field_errors": [],
                "request_id": request_id,
            },
        )
