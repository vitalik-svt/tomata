from fastapi import FastAPI, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.core import routes as main_router
from app.settings import settings

PROJECT_NAME = 'AMTA'

app = FastAPI(title=PROJECT_NAME)
app.include_router(main_router.router)
app.add_middleware(SessionMiddleware, secret_key=settings.app_fastapi_middleware_secret_key)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
    )
