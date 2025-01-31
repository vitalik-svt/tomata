from typing import Optional
import logging
import sys
import datetime as dt
import jwt

from app.core.auth import create_access_token, SECRET_KEY, ALGORITHM

from fastapi import Depends, Request, HTTPException
from fastapi.routing import APIRouter
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from starlette.templating import Jinja2Templates

from app.core.auth import authenticate_user, get_current_user
from app.core.models.user import UserInDB
from app.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/error")
async def home_route(request: Request):
    raise Exception('test exception')


@router.get("/", response_class=HTMLResponse)
async def home_route(request: Request, current_user: UserInDB = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse('/login')
    return templates.TemplateResponse("home.html", {"request": request, "current_user": current_user})


@router.get("/login", response_class=HTMLResponse)
async def login_route(request: Request, current_user: Optional[UserInDB] = Depends(get_current_user)):
    if current_user:
        return RedirectResponse('/')
    return templates.TemplateResponse("login.html", {"request": request, "current_user": current_user})


@router.get("/logout")
async def logout_route():
    response = RedirectResponse("/", status_code=302)  # redirect to home
    response.delete_cookie(key="access_token")
    return response


@router.post("/token")
async def token_route(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        return templates.TemplateResponse("login.html", {"request": request, "message": "Invalid credentials"})
    access_token = create_access_token({"sub": form_data.username}, expires_delta=settings.app_jwt_token_sec)
    response = RedirectResponse("/", status_code=302)  # redirect to home
    response.set_cookie(key="access_token", value=access_token, httponly=True, max_age=settings.app_jwt_token_sec)
    return response


@router.get("/fork_modal")
async def get_modal(request: Request):
    return templates.TemplateResponse("assignment/fork_modal.html", {"request": request})

