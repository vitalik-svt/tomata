import json
import datetime as dt
import logging

from fastapi import APIRouter, HTTPException, Depends
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from fastapi.responses import JSONResponse, HTMLResponse
from motor.motor_asyncio import AsyncIOMotorCollection

import app.core.services.database as db
from app.core.services.auth import get_current_user, require_authenticated_user
from app.core.services.assignment import (
    get_assignment_data, get_all_assignments_data, group_assignments_data,
    update_assignment, duplicate_assignment,
    get_assignment_ui_schema_from_actual_model, create_new_assignment
)
from app.core.models.assignment import AssignmentWithFullSchema, AssignmentInDB, AssignmentInUI, Status
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

    all_assignments_data = await get_all_assignments_data(collection=collection)
    grouped_assignments = group_assignments_data(all_assignments_data, group_by="group_id", sort_by=("created_at", "version"))
    _, assignment_ui_schema_hash, _ = await get_assignment_ui_schema_from_actual_model(AssignmentInUI.__name__)

    return templates.TemplateResponse(f"{prefix}/list.html", {
        "request": request,
        "current_user": current_user,
        "grouped_assignments": grouped_assignments,
        "assignment_ui_schema_hash": assignment_ui_schema_hash
    })


@router.post("/new")
async def create_new_assignment_route(
        current_user: UserInDB = Depends(require_authenticated_user),
        collection: AsyncIOMotorCollection = Depends(db.collection_dependency(settings.app_assignments_collection)),
    ):
    """
    n.b! That func should be placed in code above get/{assignment_id}, because assignment_id is str also
    so "new" can be considered as is, if it will be executed earlier
    """

    assignment = await create_new_assignment(AssignmentWithFullSchema)
    assignment.author = current_user.username

    try:
        result = await db.create_obj(assignment, collection)
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

    assignment_data = await get_assignment_data(assignment_id, collection, rename_mongo_id=True)

    # Pick schema and events_mapper, to pass separately, to not show them in UI
    assignment_ui_schema = json.loads(assignment_data.pop('assignment_ui_schema'))
    events_mapper = json.loads(assignment_data.pop('events_mapper'))

    # TODO
    # assignment.locations_to_images()

    return templates.TemplateResponse(f"{prefix}/edit.html", {
        "request": request,
        "current_user": current_user,
        "assignment": assignment_data,
        "assignment_ui_schema": assignment_ui_schema,
        "events_mapper": events_mapper
    })


@router.post("/{assignment_id}")
async def save_assignment_route(
        assignment_id: str,
        assignment_update: AssignmentInUI,
        current_user: UserInDB = Depends(require_authenticated_user),
        collection: AsyncIOMotorCollection = Depends(db.collection_dependency(settings.app_assignments_collection)),
    ):

    try:
        updated_assignment = await update_assignment(assignment_id, assignment_update, collection)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Got error updating {assignment_id}: {e}')

    return updated_assignment


@router.post("/{assignment_id}/create_new_version")
async def create_assignment_new_version_route(
        assignment_id: str,
        use_new_schema: bool = False,
        current_user: UserInDB = Depends(require_authenticated_user),
        collection: AsyncIOMotorCollection = Depends(db.collection_dependency(settings.app_assignments_collection)),
    ):

    try:
        new_assignment_id = await duplicate_assignment(assignment_id=assignment_id, collection=collection, use_new_schema = use_new_schema)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating assignment: {e}")

    return JSONResponse(content={"id": new_assignment_id})  # we will redirect to get /assignment/{assignment_id} on frontend


@router.delete("/{assignment_id}")
async def delete_assignment_route(
        assignment_id: str,
        current_user: UserInDB = Depends(require_authenticated_user),
        collection: AsyncIOMotorCollection = Depends(db.collection_dependency(settings.app_assignments_collection)),
    ):

    try:
        res = await db.delete_obj(assignment_id, collection)
    except Exception as e:
        raise HTTPException(500, f"Error deleting Assignment {assignment_id}: {e}")

    if res:
        return JSONResponse(content={"message": f"Assignment deleted successfully"})
    else:
        return JSONResponse(content={"message": f"Assignment {assignment_id} hasn't found. Nothing to delete"})



@router.get("/{assignment_id}/view")
async def view_assignment_route(
        request: Request,
        assignment_id: str,
        # we don't want to let any user see that, because they can be confused. only latest version availiable with group endpoint
        current_user: UserInDB = Depends(require_authenticated_user),
        collection: AsyncIOMotorCollection = Depends(db.collection_dependency(settings.app_assignments_collection))
):

    assignment_data = await get_assignment_data(assignment_id, collection, rename_mongo_id=True)

    return templates.TemplateResponse(f"{prefix}/view.html", {
        "request": request,
        "assignment": assignment_data,
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
    try:
        latest_assignment_id, _ = db.max_value_in_group(group_field='group_id', group_val=group_id, find_max_in_field='version', collection=collection)
        assignment_data = await get_assignment_data(latest_assignment_id, collection, rename_mongo_id=True)
    except Exception as e:
        HTTPException(500, f'Error while viewing group {group_id}: {e}')

    return templates.TemplateResponse(f"{prefix}/view.html", {
        "request": request,
        "assignment": assignment_data,
        "group_view": True,
        "current_user": current_user
    })


@router.delete("/group/{group_id}")
async def delete_group_route(
    group_id: str,
    current_user: UserInDB = Depends(require_authenticated_user),
    collection: AsyncIOMotorCollection = Depends(db.collection_dependency(settings.app_assignments_collection)),
):
    try:
        num_deleted = await db.delete_by_filter({"group_id": group_id}, collection)
    except Exception as e:
        raise HTTPException(500, f'Error while deleting group {group_id}: {e}')

    if num_deleted:
        return JSONResponse(content={"message": f"Group with {num_deleted} assignments deleted successfully"})
    else:
        return JSONResponse(content={"message": f"Group ID {group_id} doesn't exist. Nothing deleted"})

