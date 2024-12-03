from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from bson import ObjectId

import app.core.database as db
from app.core.auth import get_authenticated_user, get_password_hash
from app.core.models.user import User, UserCreate, UserInDB, Role
from app.settings import settings


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")



@router.get("/users", response_class=HTMLResponse)
async def home_route(request: Request, current_user: UserInDB = Depends(get_authenticated_user)):
    return templates.TemplateResponse("users/home.html", {
        "request": request,
        "current_user": current_user
    })


@router.get("/users/add")
async def get_add_user_page(request: Request, current_user: UserInDB = Depends(get_authenticated_user)):
    return templates.TemplateResponse("users/add.html", {
        "request": request,
        "current_user": current_user
    })


@router.post("/users/add")
async def add_user(
        username: str = Form(...),
        password: str = Form(...),
        role: str = Form(...),
        collection=Depends(db.collection_dependency(settings.app_users_collection))
    ):
    try:
        existing_user = await db.get_obj_by_field('username', username, collection)
        if existing_user:
            raise HTTPException(status_code=400, detail=f"User with username {username} already exists")

        role_enum = Role(role)
        new_user = UserInDB(
            username=username,
            hashed_password=get_password_hash(password),
            role=role_enum.value
        )
        result = await db.create_obj(new_user.model_dump(), collection)
        user_id = str(result['_id'])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating user: {e}")
    return RedirectResponse(url="/users/list", status_code=303)


@router.get("/users/list")
async def list_users(
        request: Request,
        collection=Depends(db.collection_dependency(settings.app_users_collection)),
        current_user: UserInDB = Depends(get_authenticated_user)
    ):
    users = []
    async for user in collection.find():
        user["_id"] = str(user["_id"])  # Convert ObjectId to string
        users.append(user)
    return templates.TemplateResponse("users/list.html", {
        "request": request,
        "current_user": current_user,
        "users": users
    })


@router.post("/users/delete/{user_id}")
async def delete_user(
        user_id: str,
        collection=Depends(db.collection_dependency(settings.app_users_collection)),
        current_user: UserInDB = Depends(get_authenticated_user)
    ):
    result = await collection.delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found.")
    return {"message": "User deleted successfully"}