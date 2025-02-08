import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.logger import logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging all requests and errors
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()
        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(
                "Error while operating request",
                exc_info=True,
                extra={
                    "client_ip": request.client.host,
                    "method": request.method,
                    "url": request.url.path
                }
            )
            raise e
        process_time = time.time() - start_time
        logger.info("HTTP request processed", extra={
            "client_ip": request.client.host,
            "method": request.method,
            "url": request.url.path,
            "status": response.status_code,
            "time": f"{process_time:.4f}s"
        })
        return response
