from typing import Literal, Collection, List, Tuple, Iterable, Any, Type, Union, Dict, Callable
import hashlib
import uuid
import datetime as dt
from collections import defaultdict
from pydantic import BaseModel

from motor.motor_asyncio import AsyncIOMotorCollection
from fastapi import HTTPException

from app.core.services.utils import format_date, get_model_size, get_hash
import app.core.services.database as db
import app.core.services.s3 as s3
from app.core.models.assignment import Event, EventsMapper, AssignmentInUI,AssignmentInDB, Status, AssignmentWithFullSchema, Image


def recursive_apply(data: Union[Dict, List], target_keys: Union[List[str], Tuple[str]], operation: Callable, operation_kwargs: dict = {}) -> Union[Dict, List]:
    """Recursively iterates over a dictionary or list and applies the operation in-place."""
    if isinstance(data, dict):
        for key, value in data.items():
            if key in target_keys:
                if isinstance(value, list):
                    data[key] = [operation(x, **operation_kwargs) for x in value]
                else:
                    data[key] = operation(value, **operation_kwargs)
            else:
                data[key] = recursive_apply(value, target_keys, operation, operation_kwargs)
    elif isinstance(data, list):
        for idx, item in enumerate(data):
            data[idx] = recursive_apply(item, target_keys, operation, operation_kwargs)
    return data


async def async_recursive_apply(data: Union[Dict, List], target_keys: Union[List[str], Tuple[str]], operation: Callable, operation_kwargs: dict = {}) -> Union[Dict, List]:
    """Async version of recursive apply func"""

    if isinstance(data, dict):
        for key, value in data.items():
            if key in target_keys:
                if isinstance(value, list):
                    data[key] = [await operation(x, **operation_kwargs) for x in value]
                else:
                    data[key] = await operation(value, **operation_kwargs)
            else:
                data[key] = await async_recursive_apply(value, target_keys, operation, operation_kwargs)
    elif isinstance(data, list):
        for idx, item in enumerate(data):
            data[idx] = await async_recursive_apply(item, target_keys, operation, operation_kwargs)
    return data


async def get_image_from_loc(image_data: dict, image_loc_field: str, image_data_field: str) -> dict:

    if image_data.get(image_loc_field) and len(image_data.get(image_loc_field)) > 0:
        bucket_name, prefix, file_key = s3.parse_s3_uri(image_data[image_loc_field])
        image_data[image_data_field] = await s3.s3_to_base64_image(bucket_name=bucket_name, prefix=prefix, file_key=file_key)

    return image_data


async def upload_image_to_loc(image_data: dict, assignment_id:str,  image_loc_field: str, image_data_field: str) -> dict:

    if image_data.get(image_data_field) and len(image_data.get(image_data_field)) > 0:
        s3_uri = await s3.base64_image_to_s3(
            file_name_wo_ext=get_hash(image_data[image_data_field]),
            base64_string=image_data[image_data_field],
            prefix=assignment_id
        )
        image_data[image_loc_field] = s3_uri

    return image_data


def clean_dict_field(data: dict, field_to_clean: str) -> dict:
    if data.get(field_to_clean) and len(data.get(field_to_clean)) > 0:
        data[field_to_clean] = ''
    return data


async def get_images_for_assignment_from_s3(
        assignment_data: dict,
        image_parent_keys: Tuple[str] = ('images', 'check_images'),
        image_loc_field: str = 'image_location',
        image_data_field: str = 'image_data'
) -> dict:

    """
    :param assignment_data: dict for iteration
    :param image_parent_keys: names of parent dict, where image info can be stored
    :param image_loc_field: name of attribute in image_holder, where image located
    :param image_data_field: name of attribute where base64 string of image should be stored
    :return: modified assignment_data
    """

    return await async_recursive_apply(
        data=assignment_data,
        target_keys=image_parent_keys,
        operation=get_image_from_loc,
        operation_kwargs={"image_loc_field": image_loc_field, "image_data_field": image_data_field}
    )


async def upload_images_from_assignment_to_s3(
        assignment_data: dict,
        assignment_id: str,
        image_parent_keys: Tuple[str] = ('images', 'check_images'),
        image_loc_field: str = 'image_location',
        image_data_field: str = 'image_data'
) -> dict:

    return await async_recursive_apply(
        data=assignment_data,
        target_keys=image_parent_keys,
        operation=upload_image_to_loc,
        operation_kwargs={"assignment_id": assignment_id, "image_loc_field": image_loc_field, "image_data_field": image_data_field}
    )


def clean_images_from_assignment_data(
        assignment_data: dict,
        image_parent_keys: Tuple[str] = ('images', 'check_images'),
        image_data_field: str = 'image_data'
) -> dict:

    return recursive_apply(
        data=assignment_data,
        target_keys=image_parent_keys,
        operation=clean_dict_field,
        operation_kwargs={"field_to_clean": image_data_field}
    )


async def upload_images_from_assignment_to_s3_with_clean(
        assignment_data: dict,
        assignment_id: str,
        image_parent_keys: Tuple[str] = ('images', 'check_images'),
        image_loc_field: str = 'image_location',
        image_data_field: str = 'image_data'
) -> dict:

    assignment_data = await upload_images_from_assignment_to_s3(
        assignment_data=assignment_data,
        assignment_id=assignment_id,
        image_parent_keys=image_parent_keys,
        image_loc_field=image_loc_field,
        image_data_field=image_data_field
    )

    assignment_data = clean_images_from_assignment_data(
        assignment_data=assignment_data,
        image_parent_keys=image_parent_keys,
        image_data_field=image_data_field
    )

    return assignment_data


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


async def get_assignment_data_with_images(
        assignment_id: str, collection: AsyncIOMotorCollection, as_model: bool = False, rename_mongo_id: bool = True
) -> Union[dict, AssignmentInDB]:

    assignment_data = await get_assignment_data(assignment_id=assignment_id, collection=collection, as_model=as_model, rename_mongo_id=rename_mongo_id)
    assignment_data = await get_images_for_assignment_from_s3(assignment_data=assignment_data)

    return assignment_data


async def update_assignment(assignment_id: str, data_update: dict, collection: AsyncIOMotorCollection) -> dict:

    data_update['updated_at'] = dt.datetime.now().isoformat()
    data_update['save_counter'] += 1
    data_update['size'] = get_model_size(data_update)

    del data_update['id']  # pass to update without id

    return await db.update_obj(assignment_id, data_update, collection, model_dump_kwargs={'exclude_none': True})


async def duplicate_assignment(assignment_id: str, collection: AsyncIOMotorCollection, use_new_schema: bool = True) -> str:

    # pre-create empty assignment, to know id already
    res = await db.create_obj({}, collection)
    new_assignment_id = res['_id']

    assignment_data = await get_assignment_data_with_images(assignment_id=assignment_id, collection=collection, rename_mongo_id=True)

    # on creation, we can either use schema of base assignment, or get most actual one
    if use_new_schema:
        assignment_ui_schema, assignment_ui_schema_hash, events_mapper = await get_assignment_ui_schema_from_actual_model(AssignmentInUI.__name__)
        assignment_data['assignment_ui_schema'] = assignment_ui_schema
        assignment_data['assignment_ui_schema_hash'] = assignment_ui_schema_hash
        assignment_data['events_mapper'] = events_mapper
        # create from model, to get all changed fields
        assignment_data = AssignmentWithFullSchema(**assignment_data).model_dump()

    _, latest_version = await db.max_value_in_group(
        group_field='group_id', group_val=assignment_data['group_id'], find_max_in_field='version', collection=collection
    )
    assignment_data['version'] = latest_version + 1
    assignment_data['name'] = assignment_data['name']
    assignment_data['save_counter'] = 0
    assignment_data['created_at'] = dt.datetime.now().isoformat()
    assignment_data['updated_at'] = dt.datetime.now().isoformat()

    # we need to resave all images data to new assignment_id prefix
    assignment_data = await upload_images_from_assignment_to_s3_with_clean(assignment_data=assignment_data, assignment_id=new_assignment_id)

    # updating data
    result = await db.update_obj(new_assignment_id, assignment_data, collection)

    return str(result['_id'])


async def get_all_assignments_data(
        collection: AsyncIOMotorCollection,
        needed_cols: Collection = ("group_id", "_id", "name", "status", "issue", "version", "author", "created_at", "updated_at", "size", "assignment_ui_schema_hash"),
        rename_mongo_id: bool = True,
        format_date_cols: Collection = ("created_at", "updated_at")
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


def group_assignments_data(assignments: Collection[dict[str, Any]], group_by: str = "group_id", sort_by_desc: tuple = ("updated_at", "created_at")) -> dict:

    if not assignments:
        return {}

    if sort_by_desc:
        assignments = sorted(assignments, key=lambda x: tuple(x[field] for field in sort_by_desc), reverse=True)

    grouped_assignments = defaultdict(lambda: {"assignments": [], "group_name": None})

    for assignment in assignments:
        group_id = assignment[group_by]
        group = grouped_assignments[group_id]
        if group["group_name"] is None:
            group["group_name"] = assignment.get("name")
        group["assignments"].append(assignment)

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
    assignment_ui_schema_hash = get_hash(assignment_ui_schema)
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
