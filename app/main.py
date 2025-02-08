import time
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.core.routes import core_router
from app.middlewares import LoggingMiddleware
from app.settings import settings
from app.core.services.auth import initialize_user
from app.core.services.s3 import get_s3_client, create_bucket

from app.logger import logger


PROJECT_NAME = 'TOMATA'


@asynccontextmanager
async def lifespan(app: FastAPI):
    await initialize_user(username=settings.app_init_admin_username, password=settings.app_init_admin_password)
    await create_bucket(bucket_name=settings.s3_images_bucket)
    yield


app = FastAPI(title=PROJECT_NAME, lifespan=lifespan)
app.include_router(core_router)
app.add_middleware(SessionMiddleware, secret_key=settings.app_fastapi_middleware_secret_key)
app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
    )

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(f"Ошибка в обработке запроса: {e}", exc_info=True)
        raise e
    process_time = time.time() - start_time
    logger.info(f"{request.client.host} {request.method} {request.url.path} {response.status_code} {process_time:.4f}s")
    return response

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.exception_handler(HTTPException)
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
    return templates.TemplateResponse("error.html", {"request": request, "error": str(exc)})


@app.exception_handler(Exception)
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
    return templates.TemplateResponse("error.html", {"request": request, "error": error_message, "error_traceback": error_traceback})

