from typing import Optional
import datetime as dt
import logging
import sys

from fastapi import APIRouter, HTTPException, Depends
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from fastapi.responses import JSONResponse, HTMLResponse
from motor.motor_asyncio import AsyncIOMotorCollection

import app.core.database as db
from app.core.auth import get_current_user, require_authenticated_user
from app.core.models.assignment import Assignment, assignment_default, event_type_mapper, form_schema
from app.core.models.user import UserInDB
from app.settings import settings

prefix = 'assignment'
router = APIRouter(prefix=f'/{prefix}')
templates = Jinja2Templates(directory="app/templates")

logger = logging.getLogger(__name__)


@router.get("/", response_class=HTMLResponse)
async def assignment_route(request: Request, current_user: UserInDB = Depends(require_authenticated_user)):
    return templates.TemplateResponse(f"{prefix}/home.html", {"request": request, "current_user": current_user})


@router.get("/list")
async def list_assignments_route(
        request: Request,
        current_user: UserInDB = Depends(get_current_user),  # we let any user see that
        collection: AsyncIOMotorCollection = Depends(db.collection_dependency(settings.app_assignments_collection))
    ):
    assignments = []
    async for assignment in collection.find().sort("created_at", -1):
        assignment["_id"] = str(assignment["_id"])  # Convert ObjectId to string
        assignments.append(assignment)
    return templates.TemplateResponse(f"{prefix}/list.html", {
        "request": request,
        "current_user": current_user,
        "assignments": assignments
    })


@router.get("/new")
async def create_assignment_route(
        request: Request,
        current_user: UserInDB = Depends(require_authenticated_user)
    ):
    assignment_data = assignment_default.dict(exclude_unset=True)
    assignment_data['created_at'] = dt.datetime.now().isoformat()
    assignment_data['updated_at'] = dt.datetime.now().isoformat()
    return templates.TemplateResponse(f"{prefix}/edit.html", {
        "request": request,
        "current_user": current_user,
        "assignment": assignment_data,
        "form_schema": form_schema,
        "is_edit": False,
        "event_type_mapper": event_type_mapper,
    })


@router.post("/new")
async def create_assignment_route(
        new_assignment: Assignment,
        current_user: UserInDB = Depends(require_authenticated_user),
        collection: AsyncIOMotorCollection = Depends(db.collection_dependency(settings.app_assignments_collection)),
    ):
    try:
        new_assignment_data = new_assignment.dict()
        result = await db.create_obj(new_assignment_data, collection)
        assignment_id = str(result['_id'])
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating assignment: {e}")

    return JSONResponse(content={"id": assignment_id})  # we will redirect to get /assignment/{assignment_id} on frontend


@router.get("/{assignment_id}")
async def get_assignment_route(
        request: Request,
        assignment_id: str,
        current_user: UserInDB = Depends(require_authenticated_user),
        collection: AsyncIOMotorCollection = Depends(db.collection_dependency(settings.app_assignments_collection)),
    ):
    assignment = await db.get_obj_by_id(assignment_id, collection)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return templates.TemplateResponse(f"{prefix}/edit.html", {
        "request": request,
        "current_user": current_user,
        "assignment": assignment,
        "form_schema": form_schema,
        "is_edit": bool(assignment_id),
        "event_type_mapper": event_type_mapper
    })


@router.post("/{assignment_id}")
async def save_assignment_route(
        assignment_id: str,
        updated_assignment: Assignment,
        current_user: UserInDB = Depends(require_authenticated_user),
        collection: AsyncIOMotorCollection = Depends(db.collection_dependency(settings.app_assignments_collection)),
    ):
    assignment_data = await db.get_obj_by_id(assignment_id, collection)
    if not assignment_data:
        raise HTTPException(status_code=404, detail="Assignment not found")

    updated_assignment.updated_at = dt.datetime.now().isoformat()
    updated_data_dict = updated_assignment.dict(exclude_unset=True)
    await db.update_obj(assignment_id, updated_data_dict, collection)
    return {**assignment_data, **updated_data_dict}


@router.delete("/{assignment_id}")
async def delete_assignment_route(
        assignment_id: str,
        current_user: UserInDB = Depends(require_authenticated_user),
        collection: AsyncIOMotorCollection = Depends(db.collection_dependency(settings.app_assignments_collection)),
    ):
    assignment_data = await db.get_obj_by_id(assignment_id, collection)
    if not assignment_data:
        raise HTTPException(status_code=404, detail="Assignment not found")

    await db.delete_obj(assignment_id, collection)
    return {"message": "Assignment deleted successfully"}


@router.get("/{assignment_id}/view")
async def print_page(
        request: Request,
        assignment_id: str,
        current_user: UserInDB = Depends(get_current_user),  # we let any user see that
        collection: AsyncIOMotorCollection = Depends(db.collection_dependency(settings.app_assignments_collection))
):
    assignment_data = await db.get_obj_by_id(assignment_id, collection)
    if not assignment_data:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return templates.TemplateResponse(f"{prefix}/view.html", {
        "request": request,
        "assignment_data": assignment_data,
        "current_user": current_user
    })

