import logging
from litestar import Request, Response, MediaType
from litestar.exceptions import HTTPException, ValidationException
from backend.utils.uid import new_short_id

logger = logging.getLogger("api-gateway")

import asyncio
_background_tasks: set[asyncio.Task[object]] = set()

def global_exception_handler(request: Request, exc: Exception) -> Response:
    """
    Catches ALL unhandled exceptions and returns a sanitized JSON response.
    NEVER leaks stack traces, DB schemas, or internal paths to the client.
    """
    trace_id = new_short_id(8)

    if isinstance(exc, ValidationException):
        logger.warning(f"[TRACE:{trace_id}] Validation Error: {exc.detail} - Extra: {getattr(exc, 'extra', None)}")
        # Elite V2.2: Propagate detailed validation error list to frontend to pinpoint schema mismatches
        detail_errors = exc.extra if (hasattr(exc, "extra") and exc.extra) else exc.detail
        return Response(
            media_type=MediaType.JSON,
            status_code=400,
            content={
                "detail": detail_errors,
                "errors": detail_errors,
                "trace_id": trace_id,
            },
        )

    if isinstance(exc, HTTPException) and exc.status_code < 500:
        if exc.status_code == 401 or (exc.status_code == 400 and "Invalid article ID format" in exc.detail):
            logger.debug(f"[TRACE:{trace_id}] HTTP {exc.status_code}: {exc.detail}")
        else:
            logger.warning(f"[TRACE:{trace_id}] HTTP {exc.status_code}: {exc.detail}")
        return Response(
            media_type=MediaType.JSON,
            status_code=exc.status_code,
            content={"detail": exc.detail, "trace_id": trace_id},
        )
    
    # R82.35: Graceful Disconnection (Neural Hygiene)
    # This occurs normally when a browser closes or refresh happens during a response.
    # Handle both raw RuntimeError and Litestar InternalServerException variants.
    if ("client disconnected prematurely" in str(exc).lower() or 
        (isinstance(exc, RuntimeError) and "disconnected" in str(exc).lower())):
        logger.info(f"[TRACE:{trace_id}] Client disconnected prematurely (Browser side session end).")
        return Response(
            media_type=MediaType.JSON,
            status_code=499, # Client Closed Request
            content={"detail": "Client closed connection", "trace_id": trace_id},
        )

    logger.error(f"[TRACE:{trace_id}] Unhandled {type(exc).__name__}: {exc}", exc_info=True)
    
    # Gửi cảnh báo lỗi nghiêm trọng về Telegram
    try:
        from backend.services.telegram_service import telegram_service
        import asyncio
        
        path = request.url.path if hasattr(request, "url") else "Unknown path"
        method = request.method if hasattr(request, "method") else "Unknown method"
        
        telegram_msg = (
            f"❌ <b>[SERVER ERROR - 500]</b>\n"
            f"<b>Path:</b> {method} {path}\n"
            f"<b>Trace ID:</b> <code>{trace_id}</code>\n"
            f"<b>Error:</b> <code>{type(exc).__name__}: {exc}</code>"
        )
        try:
            loop = asyncio.get_running_loop()
            task = loop.create_task(telegram_service.send_alert(telegram_msg))
            _background_tasks.add(task)
            task.add_done_callback(_background_tasks.discard)
        except RuntimeError:
            asyncio.run(telegram_service.send_alert(telegram_msg))
    except Exception as telegram_err:
        logger.warning(f"Failed to send exception alert to Telegram: {telegram_err}")

    return Response(
        media_type=MediaType.JSON,
        status_code=500,
        content={"detail": "An internal error occurred. Please contact support.", "trace_id": trace_id},
    )
