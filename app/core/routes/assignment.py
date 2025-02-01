import json
from collections import defaultdict
import datetime as dt
import logging
import uuid

from fastapi import APIRouter, HTTPException, Depends
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from fastapi.responses import JSONResponse, HTMLResponse, PlainTextResponse
from motor.motor_asyncio import AsyncIOMotorCollection

import app.core.services.database as db
from app.core.services.auth import get_current_user, require_authenticated_user
from app.core.services.utils import get_model_size
from app.core.services.assignment import get_actual_schema_data
from app.core.models.assignment import AssignmentWithSchema, AssignmentInDB, AssignmentInUI, Status
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
    # will not store all assignments, because list page will be too heavy! will fetch only necessary cols
    needed_cols = {"group_id", "_id", "name", "status", "issue", "version", "author", "created_at", "updated_at", "size"}
    # crucial to sort by version desc, created_at desc, to get latest assignment name as whole group name
    async for assignment_data in collection.find({}, needed_cols).sort([("version", -1), ("created_at", -1)]):
        assignment_data["id"] = assignment_data.pop("_id")  # convention, that we use _id only inside mongo. id for python and front
        assignments.append(assignment_data)

    grouped_assignments = defaultdict(lambda: {"assignments": [], "group_name": None})

    for assignment in assignments:
        group_id = assignment["group_id"]
        grouped_assignments[group_id]["assignments"].append(assignment)

        # Set group_name only for the first round, and set it as assignment name (latest version for each group)
        if grouped_assignments[group_id]["group_name"] is None:
            grouped_assignments[group_id]["group_name"] = assignment['name']

    return templates.TemplateResponse(f"{prefix}/list.html", {
        "request": request,
        "current_user": current_user,
        "grouped_assignments": grouped_assignments,
    })


@router.get("/schema/{assignment_class_name}")
async def get_assignment_route(
        assignment_class_name: str,
        current_user: UserInDB = Depends(require_authenticated_user)
    ):
    assignment_ui_schema, _ = await get_actual_schema_data(assignment_class_name)
    return PlainTextResponse(content=assignment_ui_schema, media_type="application/json")


# n.b! That func should be placed in code above get/{assignment_id}, because assignment_id is str also
# so "new" can be considered as is, if it will be executed earlier
@router.post("/new")
async def create_assignment_route(
        current_user: UserInDB = Depends(require_authenticated_user),
        collection: AsyncIOMotorCollection = Depends(db.collection_dependency(settings.app_assignments_collection)),
    ):

    # we always get the newest configs on creation!
    # it's json form schema for UI, so we create schema from it (without unwanted fields (assignment_ui_schema and events_mapper)
    assignment_ui_schema, events_mapper = await get_actual_schema_data(AssignmentInUI.__name__)

    assignment = AssignmentWithSchema(
        assignment_ui_schema=assignment_ui_schema,
        events_mapper=events_mapper,
        group_id=uuid.uuid4().hex,  # created only on creation of new assignment (not on copying!)
        name=f'Новое ТЗ от {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}',
        status=Status.design.value,
        issue='LM-1793',
        author=current_user.username,
        created_at=dt.datetime.now().isoformat(),
        updated_at=dt.datetime.now().isoformat(),
        description="""ОЧЕНЬ ВАЖНО!!! 
Все события, особенно GA:pageview должны отрабатывать после загрузки GTM DOM, 
в противном случае не будет слушателей разметки и данные уйдут в пустоту.

События следует отправлять на уровень document (НЕ document.body) и генерировать их через dispatchEvent.
Также необходимо добавить логирование в консоль, если enabledLogAnalytics = 1

При клике на кнопку или ссылку (clickButton, clickProduct, promoClick) - учитывать
все клики, которые приводят к переходу - левой кнопкой мыши, по колесику мыши.""",
        blocks=[],
        size=0
    )

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

    try:
        assignment_data = await db.get_obj_by_id(assignment_id, collection)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f'Got error fetching data from mongo: {e}')

    assignment_full = AssignmentInDB(**assignment_data)

    # Pick schema and events_mapper, to pass separately, to not show them in UI
    assignment_ui_schema = json.loads(assignment_full.assignment_ui_schema)
    events_mapper = json.loads(assignment_full.events_mapper)

    # and recreate model for UI (without schema ans
    assignment = AssignmentInUI(**assignment_full.model_dump(use_mongo_id=False))

    if not assignment_data:
        raise HTTPException(status_code=404, detail="Assignment not found")

    return templates.TemplateResponse(f"{prefix}/edit.html", {
        "request": request,
        "current_user": current_user,
        "assignment": assignment.model_dump(),
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
        assignment_data = await db.get_obj_by_id(assignment_id, collection)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f'Got error fetching data from mongo: {e}')

    if not assignment_data:
        raise HTTPException(status_code=404, detail="Assignment not found")

    assignment_update.updated_at = dt.datetime.now().isoformat()
    assignment_update.save_counter += 1
    assignment_update.size = get_model_size({**assignment_data, **assignment_update.model_dump(use_mongo_id=True, exclude_unset=True)})

    assignment_update_dict = assignment_update.model_dump(use_mongo_id=True, exclude_unset=True, exclude={"id"})  # never pass id in update

    try:
        await db.update_obj(assignment_id, assignment_update_dict, collection)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Got error updating {assignment_id}: {e}')


    return {**assignment_data, **assignment_update_dict}


@router.post("/{assignment_id}/create_new_version")
async def create_assignment_new_version_route(
        assignment_id: str,
        use_new_schema: bool = False,
        current_user: UserInDB = Depends(require_authenticated_user),
        collection: AsyncIOMotorCollection = Depends(db.collection_dependency(settings.app_assignments_collection)),
    ):

    try:
        base_assignment_data = await db.get_obj_by_id(assignment_id, collection)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f'Got error fetching data from mongo: {e}')

    base_assignment = AssignmentInDB(**base_assignment_data)

    # on creation, we can either use schema of base assignment, or get most actual one
    if use_new_schema:
        assignment_ui_schema, events_mapper = await get_actual_schema_data(AssignmentInUI.__name__)
        base_assignment.assignment_ui_schema=assignment_ui_schema
        base_assignment.events_mapper=events_mapper

    if not base_assignment_data:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # it's not so good to scan whole mongo collection, but we're not expecting really too much data
    _, latest_version = await db.latest_group_assignment(base_assignment.group_id, collection)

    # update base data with new version, date, etc
    new_version_assignment = AssignmentWithSchema(**base_assignment.model_dump(use_mongo_id=True))
    new_version_assignment.version = latest_version + 1
    new_version_assignment.save_counter = 0
    new_version_assignment.created_at = dt.datetime.now().isoformat()
    new_version_assignment.updated_at = dt.datetime.now().isoformat()

    try:
        result = await db.create_obj(new_version_assignment, collection)
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
        "assignment": assignment.model_dump(use_mongo_id=False),
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
    latest_assignment_id, _ = await db.latest_group_assignment(group_id, collection)
    assignment_data = await db.get_obj_by_id(latest_assignment_id, collection)
    assignment = AssignmentInDB(**assignment_data)

    if not assignment_data:
        raise HTTPException(status_code=404, detail="Group not found")

    return templates.TemplateResponse(f"{prefix}/view.html", {
        "request": request,
        "assignment": assignment.model_dump(use_mongo_id=False),
        "group_view": True,
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

