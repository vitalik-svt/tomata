from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from bson import ObjectId

import app.core.services.database as db
from app.core.services.auth import get_password_hash, require_authenticated_user
from app.core.models.user import User, UserInDB, Role
from app.settings import settings
from app.logger import logger


prefix = 'user'
router = APIRouter(prefix=f'/{prefix}')
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def home_route(request: Request, current_user: UserInDB = Depends(require_authenticated_user)):
    return templates.TemplateResponse(f"{prefix}/home.html", {
        "request": request,
        "current_user": current_user
    })


@router.get("/add")
async def add_user_route(request: Request, current_user: UserInDB = Depends(require_authenticated_user)):
    return templates.TemplateResponse(f"{prefix}/add.html", {
        "request": request,
        "current_user": current_user,
        "roles": [role.value for role in Role]
    })


@router.post("/add")
async def add_user_route(
        request: Request,
        username: str = Form(...),
        password: str = Form(...),
        role: str = Form(...),
        current_user: UserInDB = Depends(require_authenticated_user),
        collection=Depends(db.collection_dependency(settings.app_users_collection))
    ):

    username_exists = await db.get_obj_by_fields({'username': username}, collection)
    if username_exists:
        raise HTTPException(status_code=400, detail=f"User {username} already exists")

    user = User(username=username, hashed_password=get_password_hash(password), role=Role(role).value, active=True)

    try:
        user = await db.create_obj(user, collection)
        logger.info(f"User {username} ({user=}) created")
        return RedirectResponse(url=f"/{prefix}/list", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating user: {e}")


@router.get("/list")
async def list_users(
        request: Request,
        collection=Depends(db.collection_dependency(settings.app_users_collection)),
        current_user: UserInDB = Depends(require_authenticated_user)
    ):

    users = [UserInDB(**user_data) async for user_data in collection.find()]

    return templates.TemplateResponse(f"{prefix}/list.html", {
        "request": request,
        "users": users,
        "current_user": current_user
    })


@router.post("/delete/{user_id}")
async def delete_user(
        user_id: str,
        collection=Depends(db.collection_dependency(settings.app_users_collection)),
        current_user: UserInDB = Depends(require_authenticated_user)
    ):

    result = await db.delete_obj(user_id, collection)
    logger.info(f"User {user_id} deleted")

    if result:
        return {"message": f"User deleted successfully"}
    else:
        raise {"message": f"User {user_id} not found. Nothing to delete successfully"}