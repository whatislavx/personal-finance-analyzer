from __future__ import annotations

import logging
import uuid
from typing import Any, Optional

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger("app")


REQUEST_ID_HEADER = "x-request-id"


def _get_or_create_request_id(request: Request) -> str:
    rid = request.headers.get(REQUEST_ID_HEADER)
    if rid:
        return rid
    return str(uuid.uuid4())


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = _get_or_create_request_id(request)
        request.state.request_id = request_id
        try:
            response = await call_next(request)
        except Exception:
            raise
        response.headers[REQUEST_ID_HEADER] = request_id
        return response


def _json_error(*, status_code: int, message: str, request_id: Optional[str] = None, details: Any = None) -> JSONResponse:
    payload = {"message": message}
    if request_id:
        payload["request_id"] = request_id
    if details is not None:
        payload["details"] = details
    return JSONResponse(status_code=status_code, content=payload)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None) or _get_or_create_request_id(request)

    msg = exc.detail if isinstance(exc.detail, str) else "The request could not be processed. Please review the submitted data and try again."

    if exc.status_code >= 500:
        logger.exception("HTTPException %s %s rid=%s", request.method, request.url.path, request_id)
        msg = "The server encountered an internal error. Please try again later or contact support if the problem persists."
    else:
        logger.info("HTTPException %s %s status=%s rid=%s detail=%r", request.method, request.url.path, exc.status_code, request_id, exc.detail)

    return _json_error(status_code=exc.status_code, message=msg, request_id=request_id)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None) or _get_or_create_request_id(request)
    logger.info("ValidationError %s %s rid=%s errors=%s", request.method, request.url.path, request_id, exc.errors())

    return _json_error(
        status_code=422,
        message="Validation failed. Check the submitted fields and correct the highlighted values.",
        request_id=request_id,
        details=exc.errors(),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None) or _get_or_create_request_id(request)
    logger.exception("Unhandled error %s %s rid=%s", request.method, request.url.path, request_id)
    return _json_error(
        status_code=500,
        message="An unexpected server error occurred. Please try again later.",
        request_id=request_id,
    )
