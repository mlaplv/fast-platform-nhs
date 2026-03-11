import uuid
import logging
from litestar import Request, Response, MediaType
from litestar.exceptions import HTTPException, ValidationException

logger = logging.getLogger("api-gateway")

def global_exception_handler(request: Request, exc: Exception) -> Response:
    """
    Catches ALL unhandled exceptions and returns a sanitized JSON response.
    NEVER leaks stack traces, DB schemas, or internal paths to the client.
    """
    trace_id = str(uuid.uuid4())[:8]

    if isinstance(exc, HTTPException) and exc.status_code < 500:
        if exc.status_code == 401:
            logger.debug(f"[TRACE:{trace_id}] HTTP {exc.status_code}: {exc.detail}")
        else:
            logger.warning(f"[TRACE:{trace_id}] HTTP {exc.status_code}: {exc.detail}")
        return Response(
            media_type=MediaType.JSON,
            status_code=exc.status_code,
            content={"detail": exc.detail, "trace_id": trace_id},
        )
    
    if isinstance(exc, ValidationException):
        logger.warning(f"[TRACE:{trace_id}] Validation Error: {exc.detail}")
        return Response(
            media_type=MediaType.JSON,
            status_code=400,
            content={
                "detail": "Data validation failed",
                "errors": exc.extra if hasattr(exc, "extra") else str(exc),
                "trace_id": trace_id,
            },
        )

    logger.error(f"[TRACE:{trace_id}] Unhandled {type(exc).__name__}: {exc}", exc_info=True)
    return Response(
        media_type=MediaType.JSON,
        status_code=500,
        content={"detail": "An internal error occurred. Please contact support.", "trace_id": trace_id},
    )
