import json
import datetime as dt
import logging

from fastapi import APIRouter, Depends
from fastapi.templating import Jinja2Templates
from fastapi import Query
from starlette.requests import Request
from motor.motor_asyncio import AsyncIOMotorCollection

import app.core.services.database as db
from app.core.services.auth import get_current_user, require_authenticated_user
from app.core.services.assignment import get_assignment_ui_schema_from_actual_model
from app.core.models.user import UserInDB
from app.core.models.assignment import AssignmentInUI
from app.settings import settings


prefix = 'service'
router = APIRouter(prefix=f'/{prefix}')
logger = logging.getLogger(__name__)
templates = Jinja2Templates(directory="app/templates")


@router.get("/schema/{assignment_id}")
async def get_assignment_route(
        request: Request,
        assignment_id: str,
        model_class_name: str = Query(AssignmentInUI.__name__, alias="model"),
        current_user: UserInDB = Depends(require_authenticated_user),
        collection: AsyncIOMotorCollection = Depends(db.collection_dependency(settings.app_assignments_collection)),
    ):
    assignment_data = await db.get_obj_by_id(assignment_id, collection)

    assignment_ui_schema_hash = assignment_data.get('assignment_ui_schema_hash')
    assignment_ui_schema = assignment_data.get('assignment_ui_schema')
    events_mapper = assignment_data.get('events_mapper')

    assignment_data['assignment_ui_schema_hash'] = 'PLACEHOLDER'
    assignment_data['assignment_ui_schema'] = 'PLACEHOLDER'
    assignment_data['events_mapper'] = 'PLACEHOLDER'

    assignment_ui_schema_cls, assignment_ui_schema_hash_cls, events_mapper_cls = await get_assignment_ui_schema_from_actual_model(model_class_name)

    return templates.TemplateResponse(f"{prefix}/schema.html", {
        "request": request,
        "current_user": current_user,
        "assignment_id": assignment_data['_id'],
        "assignment_ui_schema_hash": assignment_ui_schema_hash,
        "assignment_ui_schema": assignment_ui_schema,
        "events_mapper": events_mapper,
        "assignment_data": json.dumps(assignment_data, indent=4, ensure_ascii=False),
        "model_class_name": model_class_name,
        "assignment_ui_schema_hash_cls": assignment_ui_schema_hash_cls,
        "assignment_ui_schema_cls": assignment_ui_schema_cls,
        "events_mapper_cls": events_mapper_cls
    })