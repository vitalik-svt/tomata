from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from bson import ObjectId

import app.core.services.database as db
from app.core.services.auth import get_password_hash, require_authenticated_user
from app.core.models.user import User, UserInDB, Role
from app.settings import settings


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
async def get_add_user_page(request: Request, current_user: UserInDB = Depends(require_authenticated_user)):
    return templates.TemplateResponse(f"{prefix}/add.html", {
        "request": request,
        "current_user": current_user,
        "roles": [role.value for role in Role]
    })


@router.post("/add")
async def add_user(
        request: Request,
        username: str = Form(...),
        password: str = Form(...),
        role: str = Form(...),
        current_user: UserInDB = Depends(require_authenticated_user),
        collection=Depends(db.collection_dependency(settings.app_users_collection))
    ):

    existing_user = await db.get_obj_by_fields({'username': username}, collection)
    if existing_user:
        raise HTTPException(status_code=400, detail=f"User with username {username} already exists")

    role_enum = Role(role)
    new_user = User(
        username=username,
        hashed_password=get_password_hash(password),
        role=role_enum.value,
        active=True  # create active user by default
    )
    await db.create_obj(new_user.model_dump(), collection)

    return RedirectResponse(url=f"/{prefix}/list", status_code=303)


@router.get("/list")
async def list_users(
        request: Request,
        collection=Depends(db.collection_dependency(settings.app_users_collection)),
        current_user: UserInDB = Depends(require_authenticated_user)
    ):
    users = []
    async for user_data in collection.find():
        user = UserInDB(**user_data)
        users.append(user)
    return templates.TemplateResponse(f"{prefix}/list.html", {
        "request": request,
        "current_user": current_user,
        "users": users
    })


@router.post("/delete/{user_id}")
async def delete_user(
        user_id: str,
        collection=Depends(db.collection_dependency(settings.app_users_collection)),
        current_user: UserInDB = Depends(require_authenticated_user)
    ):
    result = await collection.delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found.")
    return {"message": "User deleted successfully"}