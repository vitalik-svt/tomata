from typing import Union, List, Tuple
import pydantic
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection, AsyncIOMotorDatabase
from bson import ObjectId
from app.settings import settings


async def get_db(db_name: str = settings.mongo_initdb_database, uri: str = settings.mongo_uri) -> AsyncIOMotorDatabase:
    client = AsyncIOMotorClient(uri)
    return client[db_name]


async def get_collection(
        db_name: str = settings.mongo_initdb_database,
        collection_name: str = settings.app_assignments_collection
) -> AsyncIOMotorCollection:
    db = await get_db(db_name)
    return db[collection_name]


def collection_dependency(collection_name: str, db_name: str = settings.mongo_initdb_database):
    """dependency just in case"""
    async def _get_collection():
        return await get_collection(db_name=db_name, collection_name=collection_name)
    return _get_collection


async def get_obj_by_id(obj_id: str, collection: AsyncIOMotorCollection):
    obj = await collection.find_one({"_id": ObjectId(obj_id)})
    if obj:
        obj["_id"] = str(obj["_id"])
    return obj


async def get_obj_by_fields(query: dict, collection: AsyncIOMotorCollection, filter_cols: Union[Tuple, List] = None, find_many: bool = False) -> Union[dict, List[dict]]:
    if "_id" in query and isinstance(query["_id"], str):
        query["_id"] = ObjectId(query["_id"])

    if find_many:
        objs = [obj async for obj in collection.find(query, filter_cols)]
        if objs:
            for obj in objs:
                obj["_id"] = str(obj["_id"])
        return objs

    else:
        obj = await collection.find_one(query, filter_cols)
        if obj:
            obj["_id"] = str(obj["_id"])
        return obj


async def create_obj(obj: dict | pydantic.BaseModel, collection: AsyncIOMotorCollection, model_dump_kwargs: dict = None):
    if isinstance(obj, pydantic.BaseModel):
        model_dump_kwargs = model_dump_kwargs if model_dump_kwargs else {}
        obj = obj.model_dump(**model_dump_kwargs)

    result = await collection.insert_one(obj)
    obj_id = str(result.inserted_id)
    obj = await collection.find_one({"_id": ObjectId(obj_id)})
    return obj


async def update_obj(
        obj_id: str, obj: dict | pydantic.BaseModel, collection: AsyncIOMotorCollection, model_dump_kwargs: dict = None
) -> dict | pydantic.BaseModel | None:

    if isinstance(obj, pydantic.BaseModel):
        model_dump_kwargs = model_dump_kwargs if model_dump_kwargs else {}
        obj = obj.model_dump(**model_dump_kwargs)

    # never pass id in updates
    if obj.get("_id"):
        del obj["_id"]

    result = await collection.update_one(
        {"_id": ObjectId(obj_id)},
        {"$set": obj}
    )
    if result.matched_count > 0:
        obj["_id"] = obj_id
        return obj
    return None


async def delete_obj(obj_id: str, collection: AsyncIOMotorCollection) -> int | None:
    result = await collection.delete_one({"_id": ObjectId(obj_id)})
    return result.deleted_count if result.deleted_count > 0 else None


async def delete_by_filter(filter: dict, collection: AsyncIOMotorCollection) -> int | None:
    result = await collection.delete_many(filter)
    return result.deleted_count if result.deleted_count > 0 else None


async def max_value_in_group(
        group_field: str, group_val: str, find_max_in_field: str, collection: AsyncIOMotorCollection
) -> tuple[str | None, str | int]:

    pipeline = [
        {"$match": {group_field: group_val}},
        {"$sort": {find_max_in_field: -1}},
        {"$limit": 1},
    ]
    result = await collection.aggregate(pipeline).to_list(length=1)

    if result:
        return result[0]["_id"], result[0][find_max_in_field]
    else:
        return None, 0

