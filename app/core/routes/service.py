import json
import datetime as dt
import logging

from fastapi import APIRouter, HTTPException, Depends
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from fastapi.responses import JSONResponse, HTMLResponse, PlainTextResponse
from motor.motor_asyncio import AsyncIOMotorCollection

import app.core.services.database as db
from app.core.services.auth import get_current_user, require_authenticated_user
from app.core.services.assignment import get_assignment_ui_schema_from_actual_model
from app.core.models.user import UserInDB
from app.settings import settings


prefix = 'service'
router = APIRouter(prefix=f'/{prefix}')
logger = logging.getLogger(__name__)


@router.get("/schema/model/{assignment_class_name}")
async def get_assignment_route(
        assignment_class_name: str,
        current_user: UserInDB = Depends(require_authenticated_user)
    ):
    assignment_ui_schema, assignment_ui_schema_hash, events_mapper = await get_assignment_ui_schema_from_actual_model(assignment_class_name)
    return PlainTextResponse(
        content=f"""{assignment_class_name} schema:{'\n'*2}
Hash: {assignment_ui_schema_hash}
{'\n'*2}
{assignment_ui_schema}
{'\n'*2}
{events_mapper}
""",
        media_type="application/json"
    )


@router.get("/schema/{assignment_id}")
async def get_assignment_route(
        assignment_id: str,
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

    return PlainTextResponse(
        content=f"""assignment_id {assignment_data['_id']} schema:{'\n'*2}
Hash: {assignment_ui_schema_hash}
{'\n'*2}
{assignment_ui_schema}
{'\n'*2}
{events_mapper}
{'\n'*2}
{json.dumps(assignment_data, indent=4, ensure_ascii=False)}
""",
        media_type="application/json"
    )
