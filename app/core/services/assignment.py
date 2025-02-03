from typing import Literal, Collection, List, Tuple, Iterable, Any, Type, Union
import hashlib
import uuid
import datetime as dt
import pandas as pd
from pydantic import BaseModel

from motor.motor_asyncio import AsyncIOMotorCollection
from fastapi import HTTPException

from app.core.services.utils import format_date, get_model_size
import app.core.services.database as db
from app.core.models.assignment import Event, EventsMapper, AssignmentInUI,AssignmentInDB, Status, AssignmentWithFullSchema


async def get_assignment_data(
        assignment_id: str, collection: AsyncIOMotorCollection, as_model: bool = False, rename_mongo_id: bool = True
) -> Union[dict, AssignmentInDB]:

    assignment_data = await db.get_obj_by_id(assignment_id, collection)
    if not assignment_data:
        raise HTTPException(status_code=404, detail="Assignment not found")

    if rename_mongo_id:
        assignment_data['id'] = assignment_data.pop('_id')

    if as_model:
        return AssignmentInDB(**assignment_data)
    else:
        return assignment_data


async def update_assignment(assignment_id: str, assignment_update: AssignmentInUI, collection: AsyncIOMotorCollection) -> dict:

    # TODO
    # assignment_update.images_to_locations

    assignment_update.updated_at = dt.datetime.now().isoformat()
    assignment_update.save_counter += 1
    assignment_update.size = get_model_size(assignment_update)

    del assignment_update.id  # pass to update without id

    return await db.update_obj(assignment_id, assignment_update, collection)


async def duplicate_assignment(assignment_id: str, collection: AsyncIOMotorCollection, use_new_schema: bool = True) -> str:

    assignment_data = await get_assignment_data(assignment_id, collection)

    try:
        # on creation, we can either use schema of base assignment, or get most actual one
        if use_new_schema:
            assignment_ui_schema, assignment_ui_schema_hash, events_mapper = await get_assignment_ui_schema_from_actual_model(AssignmentInUI.__name__)
            assignment_data['assignment_ui_schema'] = assignment_ui_schema
            assignment_data['assignment_ui_schema_hash'] = assignment_ui_schema_hash
            assignment_data['events_mapper'] = events_mapper

        _, latest_version = await db.max_value_in_group(
            group_field='group_id', group_val=assignment_data['group_id'], find_max_in_field='version', collection=collection
        )
        assignment_data['version'] = latest_version + 1
        assignment_data['save_counter'] = 0
        assignment_data['created_at'] = dt.datetime.now().isoformat()
        assignment_data['updated_at'] = dt.datetime.now().isoformat()

        result = await db.create_obj(assignment_data, collection)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error while creating new version: {e}")

    return str(result['_id'])



async def get_all_assignments_data(
        collection: AsyncIOMotorCollection,
        needed_cols: Collection = ("group_id", "_id", "name", "status", "issue", "version", "author", "created_at", "updated_at", "size", "assignment_ui_schema_hash"),
        rename_mongo_id: bool = True,
        format_date_cols: Collection = None
) -> List[dict[str, Any]]:

    """
    Just collects all data as List of dicts from mongo, with needed fields
    """

    assignments = []
    async for assignment_data in collection.find({}, needed_cols):
        if rename_mongo_id:
            assignment_data["id"] = assignment_data.pop("_id")  # convention, that we use _id only inside mongo. id for python and front
        if format_date_cols:
            for col in format_date_cols:
                assignment_data[col] = format_date(assignment_data[col])
        assignments.append(assignment_data)

    return assignments


def group_assignments_data(assignments: Collection[dict[str, Any]], group_by: str, sort_by: Collection = None) -> dict:

    if not assignments:
        return {}

    df = pd.DataFrame(assignments)
    grouped_assignments = {}

    for group_id, group in df.groupby(group_by):
        if sort_by:
            group = group.sort_values(by=list(sort_by), ascending=[False] * len(sort_by))
        grouped_assignments[group_id] = {
            "assignments": group.to_dict(orient="records"),
            "group_name": group.iloc[0]["name"] if "name" in group.columns else None
        }

    return grouped_assignments


async def get_assignment_ui_schema_from_actual_model(
        assignment_class_name: str = Literal['AssignmentInUI', 'AssignmentInDB', 'AssignmentWithSchema', 'AssignmentBase']
) -> tuple[str, str, str]:
    """
    Updating all json descriptions (because it's base for Json Form creation) with most actual data
    Getting Schema and Events mapper (both in json string) to pass it to Front
    """

    Event.update_json_schema_for_field('event_type', {"enum": list((await EventsMapper.from_yaml()).dump().keys())})
    eval(assignment_class_name).update_json_schema_for_field('status', {"enum": [status.value for status in Status]})

    assignment_ui_schema = eval(assignment_class_name).dump_schema(return_str=True)
    assignment_ui_schema_hash = hashlib.md5(assignment_ui_schema.encode()).hexdigest()
    events_mapper = (await EventsMapper.from_yaml()).dump(return_str=True)

    return assignment_ui_schema, assignment_ui_schema_hash, events_mapper


async def create_new_assignment(assignment_model_class: Type[BaseModel] = AssignmentWithFullSchema) -> BaseModel:

    # we always get the newest configs on creation!
    # it's json form schema for UI, so we create schema from it (without unwanted fields (assignment_ui_schema and events_mapper)
    assignment_ui_schema, assignment_ui_schema_hash, events_mapper = await get_assignment_ui_schema_from_actual_model(AssignmentInUI.__name__)

    assignment = assignment_model_class(
        assignment_ui_schema=assignment_ui_schema,
        assignment_ui_schema_hash=assignment_ui_schema_hash,
        events_mapper=events_mapper,
        group_id=uuid.uuid4().hex,  # created only on creation of new assignment (not on copying!)
        name=f'Новое ТЗ от {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}',
        status=Status.design.value,
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
        blocks=[],
        size=0
    )

    return assignment
