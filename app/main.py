from fastapi import FastAPI, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.routes import core_router
from app.settings import settings
from app.core.auth import initialize_admin_user

PROJECT_NAME = 'AMTA'

app = FastAPI(title=PROJECT_NAME)
app.include_router(core_router)
app.add_middleware(SessionMiddleware, secret_key=settings.app_fastapi_middleware_secret_key)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
    )

app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.on_event("startup")
async def startup_event():
    await initialize_admin_user()
