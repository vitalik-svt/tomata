import json
import pprint
from typing import Optional
from collections import defaultdict
import datetime as dt
import logging
import sys
import uuid

from fastapi import APIRouter, HTTPException, Depends
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from fastapi.responses import JSONResponse, HTMLResponse
from motor.motor_asyncio import AsyncIOMotorCollection

import app.core.database as db
from app.utils import get_model_size
from app.core.auth import get_current_user, require_authenticated_user
from app.core.models.assignment import AssignmentNew, AssignmentInDB
from app.core.schema import get_events_mapper, get_assignment_schema
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
    async for assignment_data in collection.find().sort("version", -1):  # sort by version desc!
        assignments.append(AssignmentInDB(**assignment_data))

    grouped_assignments = defaultdict(lambda: {"assignments": [], "group_name": None})

    for assignment in assignments:
        group_id = assignment.group_id
        grouped_assignments[group_id]["assignments"].append(assignment)

        # Set group_name only for the first assignment (latest version for each group)
        if grouped_assignments[group_id]["group_name"] is None:
            grouped_assignments[group_id]["group_name"] = assignment.name

    return templates.TemplateResponse(f"{prefix}/list.html", {
        "request": request,
        "current_user": current_user,
        "grouped_assignments": grouped_assignments,
    })


@router.get("/new")
async def create_assignment_route(
        request: Request,
        current_user: UserInDB = Depends(require_authenticated_user)
    ):

    # on creation we always get newest configs!
    assignment_schema = get_assignment_schema()
    events_mapper = get_events_mapper()

    assignment = AssignmentNew(
        assignment_schema=json.dumps(assignment_schema, indent=4, ensure_ascii=False),
        events_mapper=json.dumps(events_mapper, indent=4, ensure_ascii=False),
        name='Новое ТЗ',
        author=current_user.username,
        issue='LM-1793',
        created_at=dt.datetime.now().isoformat(),
        updated_at=dt.datetime.now().isoformat(),
        description="""ОЧЕНЬ ВАЖНО!!! 
Все события, особенно GA:pageview должны отрабатывать после загрузки GTM DOM, 
в противном случае не будет слушателей разметки и данные уйдут в пустоту.

События следует отправлять на уровень document (НЕ document.body) и генерировать их через dispatchEvent.
Также необходимо добавить логирование в консоль, если enabledLogAnalytics = 1

При клике на кнопку или ссылку (clickButton, clickProduct, promoClick) - учитывать
все клики, которые приводят к переходу - левой кнопкой мыши, по колесику мыши.""",
        blocks=[]
    )

    return templates.TemplateResponse(f"{prefix}/edit.html", {
        "request": request,
        "current_user": current_user,
        "assignment": assignment.model_dump(by_alias=True, exclude_unset=True),
        "assignment_schema": assignment_schema,
        "events_mapper": events_mapper,
        "is_edit": False,
    })


@router.post("/new")
async def create_assignment_route(
        new_assignment: AssignmentNew,
        current_user: UserInDB = Depends(require_authenticated_user),
        collection: AsyncIOMotorCollection = Depends(db.collection_dependency(settings.app_assignments_collection)),
    ):
    try:

        new_assignment.group_id = uuid.uuid4().hex  # created only on creation of new assignment (not on copying!)
        new_assignment.weight_mb = get_model_size(new_assignment)

        new_assignment_data = new_assignment.model_dump(by_alias=True)  # crucial!

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

    try:
        assignment_data = await db.get_obj_by_id(assignment_id, collection)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f'Got error fetching data from mongo: {e}')

    assignment = AssignmentInDB(**assignment_data)

    assignment_schema = json.loads(assignment.assignment_schema)
    events_mapper = json.loads(assignment.events_mapper)


    if not assignment_data:
        raise HTTPException(status_code=404, detail="Assignment not found")

    return templates.TemplateResponse(f"{prefix}/edit.html", {
        "request": request,
        "current_user": current_user,
        "assignment": assignment.model_dump(),
        "assignment_schema": assignment_schema,
        "events_mapper": events_mapper,
        "is_edit": bool(assignment_id)
    })


@router.post("/{assignment_id}")
async def save_assignment_route(
        assignment_id: str,
        assignment_update: AssignmentInDB,
        current_user: UserInDB = Depends(require_authenticated_user),
        collection: AsyncIOMotorCollection = Depends(db.collection_dependency(settings.app_assignments_collection)),
    ):

    try:
        assignment_data = await db.get_obj_by_id(assignment_id, collection)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f'Got error fetching data from mongo: {e}')

    if not assignment_data:
        raise HTTPException(status_code=404, detail="Assignment not found")

    assignment_update.updated_at = dt.datetime.now().isoformat()
    assignment_update.save_counter += 1
    assignment_update.weight_mb = get_model_size({**assignment_data, **assignment_update.model_dump(by_alias=True, exclude_unset=True)})

    assignment_update_dict = assignment_update.model_dump(by_alias=True, exclude_unset=True, exclude={"id"})  # never pass id in update

    try:
        await db.update_obj(assignment_id, assignment_update_dict, collection)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Got error updating {assignment_id}: {e}')


    return {**assignment_data, **assignment_update_dict}


@router.post("/{assignment_id}/create_new_version")
async def create_assignment_new_version_route(
        assignment_id: str,
        use_new_schema: bool,
        current_user: UserInDB = Depends(require_authenticated_user),
        collection: AsyncIOMotorCollection = Depends(db.collection_dependency(settings.app_assignments_collection)),
    ):

    # get base data
    try:
        base_assignment_data = await db.get_obj_by_id(assignment_id, collection)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f'Got error fetching data from mongo: {e}')

    base_assignment = AssignmentInDB(**base_assignment_data)

    # on creation, we can either use schema of base assignment, or get most actual one
    if use_new_schema:
        base_assignment.assignment_schema = json.dumps(get_assignment_schema(), indent=4, ensure_ascii=False)
        base_assignment.events_mapper = json.dumps(get_events_mapper(), indent=4, ensure_ascii=False)

    if not base_assignment_data:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # it's not so good to scan whole mongo collection, but we're not expecting really too much data
    _, latest_version = await db.latest_group_assignment(base_assignment.group_id, collection)

    # update base data with new version, date, etc
    new_version_assignment = AssignmentNew(**base_assignment.model_dump())
    new_version_assignment.version = latest_version + 1
    new_version_assignment.save_counter = 0
    new_version_assignment.created_at = dt.datetime.now().isoformat()
    new_version_assignment.updated_at = dt.datetime.now().isoformat()

    try:
        new_assignment_data = new_version_assignment.model_dump(by_alias=True)
        result = await db.create_obj(new_assignment_data, collection)
        new_assignment_id = str(result['_id'])
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating assignment: {e}")

    return JSONResponse(content={"id": new_assignment_id})  # we will redirect to get /assignment/{assignment_id} on frontend



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

    return {"message": f"Assignment {assignment_id} deleted successfully"}


@router.get("/{assignment_id}/view")
async def view_assignment_route(
        request: Request,
        assignment_id: str,
        current_user: UserInDB = Depends(get_current_user),  # we let any user see that
        collection: AsyncIOMotorCollection = Depends(db.collection_dependency(settings.app_assignments_collection))
):
    assignment_data = await db.get_obj_by_id(assignment_id, collection)
    assignment = AssignmentInDB(**assignment_data)

    if not assignment_data:
        raise HTTPException(status_code=404, detail="Assignment not found")

    return templates.TemplateResponse(f"{prefix}/view.html", {
        "request": request,
        "assignment": assignment.model_dump(),
        "current_user": current_user
    })


@router.get("/group/{group_id}/view")
async def view_latest_assignment_route(
        request: Request,
        group_id: str,
        current_user: UserInDB = Depends(get_current_user),  # we let any user see that
        collection: AsyncIOMotorCollection = Depends(db.collection_dependency(settings.app_assignments_collection))
):
    latest_assignment_id, _ = await db.latest_group_assignment(group_id, collection)
    assignment_data = await db.get_obj_by_id(latest_assignment_id, collection)
    assignment = AssignmentInDB(**assignment_data)

    if not assignment_data:
        raise HTTPException(status_code=404, detail="Group not found")

    return templates.TemplateResponse(f"{prefix}/view.html", {
        "request": request,
        "assignment": assignment.model_dump(),
        "current_user": current_user
    })


@router.delete("/group/{group_id}")
async def delete_group_route(
    group_id: str,
    current_user: UserInDB = Depends(require_authenticated_user),
    collection: AsyncIOMotorCollection = Depends(db.collection_dependency(settings.app_assignments_collection)),
):
    # Fetch all assignment IDs for the given group_id
    assignment_ids = [str(doc["_id"]) async for doc in collection.find({"group_id": group_id}, {"_id": 1})]

    if not assignment_ids:
        raise HTTPException(status_code=404, detail=f"No assignments found for group_id {group_id}")

    delete_result = await collection.delete_many({"group_id": group_id})

    return {"message": f"Deleted {delete_result.deleted_count} assignments successfully"}

