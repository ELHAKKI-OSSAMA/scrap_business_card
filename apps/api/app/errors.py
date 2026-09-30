from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class ApiError(Exception):
    """Error with a stable machine-readable ``code`` (translated client-side)."""

    def __init__(self, status: int, code: str, message: str, details: dict | None = None):
        self.status = status
        self.code = code
        self.message = message
        self.details = details or {}


def _body(code: str, message: str, details: dict | None = None, request_id: str | None = None) -> dict:
    return {"error": {"code": code, "message": message, "details": details or {}, "request_id": request_id}}


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api(request: Request, exc: ApiError):
        return JSONResponse(status_code=exc.status, content=_body(exc.code, exc.message, exc.details, getattr(request.state, "request_id", None)))

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError):
        errors = [{"loc": list(e.get("loc", [])), "msg": e.get("msg"), "type": e.get("type")} for e in exc.errors()]
        return JSONResponse(status_code=422, content=_body("validation_error", "Request validation failed.", {"errors": errors}, getattr(request.state, "request_id", None)))

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException):
        code = {401: "unauthorized", 403: "forbidden", 404: "not_found", 405: "method_not_allowed"}.get(exc.status_code, "http_error")
        return JSONResponse(status_code=exc.status_code, content=_body(code, str(exc.detail), None, getattr(request.state, "request_id", None)), headers=getattr(exc, "headers", None))

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception):
        import logging

        logging.getLogger("app").exception("unhandled error", extra={"request_id": getattr(request.state, "request_id", None)})
        return JSONResponse(status_code=500, content=_body("internal_error", "An unexpected error occurred.", None, getattr(request.state, "request_id", None)))
