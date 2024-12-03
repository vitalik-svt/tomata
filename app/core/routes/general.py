import logging

from fastapi import Depends, Request
from fastapi.routing import APIRouter
from fastapi.responses import HTMLResponse
from starlette.templating import Jinja2Templates

from app.core.auth import get_authenticated_user
from app.core.models.user import UserInDB

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def home(request: Request, current_user: UserInDB = Depends(get_authenticated_user)):
    return templates.TemplateResponse("welcome.html", {"request": request, "current_user": current_user})
