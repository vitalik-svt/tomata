from typing import Callable, Any
import json
import datetime as dt

from fastapi import APIRouter, HTTPException, Depends
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from fastapi.responses import JSONResponse, HTMLResponse
from motor.motor_asyncio import AsyncIOMotorCollection

import app.core.services.database as db
import app.core.services.s3 as s3
from app.core.services.auth import get_current_user, require_authenticated_user
from app.core.services.assignment import (
    get_assignment_data_with_images, get_all_assignments_data, group_assignments_data,
    update_assignment_in_db, duplicate_assignment, update_assignment_size_total,
    get_actual_model_schema_data, create_new_assignment,
    upload_images_from_assignment_to_s3_with_clean, del_assignment_with_images,
    del_group_of_assignments_with_images
)
from app.core.models.assignment import AssignmentWithFullSchema, AssignmentInUI, Event
from app.core.models.user import UserInDB
from app.settings import settings
from app.logger import logger

prefix = 'assignment'
router = APIRouter(prefix=f'/{prefix}')
templates = Jinja2Templates(directory="app/templates")



@router.get("/", response_class=HTMLResponse)
async def assignment_route(request: Request, current_user: UserInDB = Depends(require_authenticated_user)):
    return templates.TemplateResponse(f"{prefix}/home.html", {"request": request, "current_user": current_user})


@router.get("/list")
async def list_assignments_route(
        request: Request,
        current_user: UserInDB = Depends(get_current_user),  # we let any user see that
        collection: AsyncIOMotorCollection = Depends(db.collection_dependency(settings.app_assignments_collection))
    ):

    all_assignments_data = await get_all_assignments_data(collection=collection)
    grouped_assignments = group_assignments_data(all_assignments_data)
    _, actual_assignment_ui_schema_hash, _ = await get_actual_model_schema_data()

    return templates.TemplateResponse(f"{prefix}/list.html", {
        "request": request,
        "current_user": current_user,
        "grouped_assignments": grouped_assignments,
        "actual_assignment_ui_schema_hash": actual_assignment_ui_schema_hash
    })


@router.post("/new")
async def create_new_assignment_route(
        current_user: UserInDB = Depends(require_authenticated_user),
        collection: AsyncIOMotorCollection = Depends(db.collection_dependency(settings.app_assignments_collection)),
    ):
    """
    n.b! That func should be placed in code above post/{assignment_id}, because assignment_id is str also
    so "new" can be considered as assignment_id.
    """

    assignment = await create_new_assignment(AssignmentWithFullSchema)
    assignment.author = current_user.username

    result = await db.create_obj(assignment, collection)
    assignment_id = str(result['_id'])

    return JSONResponse(content={"id": assignment_id})  # we will redirect to get /assignment/{assignment_id} on frontend


@router.get("/{assignment_id}")
async def get_assignment_route(
        request: Request,
        assignment_id: str,
        current_user: UserInDB = Depends(require_authenticated_user),
        collection: AsyncIOMotorCollection = Depends(db.collection_dependency(settings.app_assignments_collection)),
    ):

    assignment_data = await get_assignment_data_with_images(assignment_id=assignment_id, collection=collection, rename_mongo_id=True)
    # Pop schema and events_mapper, to pass separately, to not show them in UI data itself
    assignment_ui_schema = json.loads(assignment_data.pop('assignment_ui_schema'))
    events_mapper = json.loads(assignment_data.pop('events_mapper'))

    return templates.TemplateResponse(f"{prefix}/edit.html", {
        "request": request,
        "current_user": current_user,
        "assignment_data": assignment_data,
        "assignment_ui_schema": assignment_ui_schema,
        "events_mapper": events_mapper
    })


@router.post("/{assignment_id}")
async def save_assignment_route(
        assignment_id: str,
        assignment_update: dict,
        current_user: UserInDB = Depends(require_authenticated_user),
        collection: AsyncIOMotorCollection = Depends(db.collection_dependency(settings.app_assignments_collection)),
    ):

    updated_assignment = update_assignment_size_total(data=assignment_update)
    updated_assignment = await upload_images_from_assignment_to_s3_with_clean(assignment_data=updated_assignment, assignment_id=assignment_id)
    updated_assignment = await update_assignment_in_db(assignment_id=assignment_id, data_update=updated_assignment, collection=collection)

    return updated_assignment


@router.post("/{assignment_id}/create_new_version")
async def create_assignment_new_version_route(
        assignment_id: str,
        use_new_schema: bool = False,
        current_user: UserInDB = Depends(require_authenticated_user),
        collection: AsyncIOMotorCollection = Depends(db.collection_dependency(settings.app_assignments_collection)),
    ):

    new_assignment_id = await duplicate_assignment(assignment_id=assignment_id, collection=collection, use_new_schema=use_new_schema)

    return JSONResponse(content={"id": new_assignment_id})  # we will redirect to get /assignment/{assignment_id} on frontend


@router.delete("/{assignment_id}")
async def delete_assignment_route(
        assignment_id: str,
        current_user: UserInDB = Depends(require_authenticated_user),
        collection: AsyncIOMotorCollection = Depends(db.collection_dependency(settings.app_assignments_collection)),
    ):

    del_assignment, del_assignment_images = await del_assignment_with_images(assignment_id=assignment_id, collection=collection)

    if del_assignment:
        return JSONResponse(content={"message": f"Assignment deleted successfully with {del_assignment_images} images"})
    else:
        return JSONResponse(content={"message": f"Assignment {assignment_id} hasn't found. Nothing to delete"})



@router.get("/{assignment_id}/view")
async def view_assignment_route(
        request: Request,
        assignment_id: str,
        # we don't want to let any user see that, because they can be confused. Only latest version availiable with group endpoint
        current_user: UserInDB = Depends(require_authenticated_user),
        collection: AsyncIOMotorCollection = Depends(db.collection_dependency(settings.app_assignments_collection))
):

    assignment_data = await get_assignment_data_with_images(assignment_id, collection, rename_mongo_id=True)

    return templates.TemplateResponse(f"{prefix}/view.html", {
        "request": request,
        "assignment_data": assignment_data,
        "group_view": False,
        "current_user": current_user
    })


@router.get("/group/{group_id}/view")
async def view_latest_assignment_route(
        request: Request,
        group_id: str,
        current_user: UserInDB = Depends(get_current_user),  # we let any user see that
        collection: AsyncIOMotorCollection = Depends(db.collection_dependency(settings.app_assignments_collection))
):

    latest_assignment_id, _ = await db.max_value_in_group(group_field='group_id', group_val=group_id, find_max_in_field='version', collection=collection)
    assignment_data = await get_assignment_data_with_images(latest_assignment_id, collection, rename_mongo_id=True)

    return templates.TemplateResponse(f"{prefix}/view.html", {
        "request": request,
        "assignment_data": assignment_data,
        "group_view": True,
        "current_user": current_user
    })


@router.delete("/group/{group_id}")
async def delete_group_route(
    group_id: str,
    current_user: UserInDB = Depends(require_authenticated_user),
    collection: AsyncIOMotorCollection = Depends(db.collection_dependency(settings.app_assignments_collection)),
):

    num_deleted_docs, deleted_images_num = await del_group_of_assignments_with_images(group_id=group_id, collection=collection)

    if num_deleted_docs:
        return JSONResponse(content={"message": f"Group ({num_deleted_docs} assignments, {deleted_images_num} images) deleted successfully"})
    else:
        return JSONResponse(content={"message": f"Group ID {group_id} doesn't exist. Nothing deleted"})

