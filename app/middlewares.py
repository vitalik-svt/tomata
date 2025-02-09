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
            logger.error(f"Error while operating request {request.method} {request.url.path} from {request.client.host}: {e}", exc_info=True)
            raise e
        process_time = time.time() - start_time
        logger.debug(f"HTTP request {request.method} {request.url.path} from {request.client.host} processed for {process_time:.4f}s with {response.status_code}")
        return response
