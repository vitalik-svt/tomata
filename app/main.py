from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.core.routes import core_router
from app.middlewares import LoggingMiddleware
from app.settings import settings
from app.core.services.auth import initialize_user
from app.core.services.s3 import create_bucket
from app.exceptions import general_exception_handler, http_exception_handler


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
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)


app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")
