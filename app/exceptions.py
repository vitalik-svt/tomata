import traceback
from fastapi import Request, HTTPException
from fastapi.templating import Jinja2Templates

from app.core.services.auth import get_current_user
from app.logger import logger


templates = Jinja2Templates(directory="app/templates")


async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(
        f"Error {type(exc).__name__}: {str(exc)}",
        exc_info=True,
        extra={
            "client_ip": request.client.host,
            "method": request.method,
            "url": request.url.path
        }
    )
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "error": str(exc),
            "current_user": await get_current_user(request)
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    error_message = str(exc)
    error_traceback = traceback.format_exc()
    logger.error(
        f"Error {type(exc).__name__}: {str(exc)}",
        exc_info=True,
        extra={
            "client_ip": request.client.host,
            "method": request.method,
            "url": request.url.path
        }
    )
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "error": error_message,
            "error_traceback": error_traceback,
            "current_user": await get_current_user(request)
        }
    )

