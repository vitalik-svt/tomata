from typing import Any, Union, List
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection, AsyncIOMotorDatabase
from bson import ObjectId
from app.settings import settings



async def get_db(db_name: str = settings.mongo_initdb_database, uri: str = settings.get_mongo_uri) -> AsyncIOMotorDatabase:
    client = AsyncIOMotorClient(uri)
    return client[db_name]


async def get_collection(
        db_name: str = settings.mongo_initdb_database,
        collection_name: str = settings.app_assignments_collection
) -> AsyncIOMotorCollection:
    db = await get_db(db_name)
    return db[collection_name]


def collection_dependency(collection_name: str, db_name: str = settings.mongo_initdb_database):
    async def _get_collection():
        return await get_collection(db_name=db_name, collection_name=collection_name)
    return _get_collection


async def get_obj_by_id(obj_id: str, collection: AsyncIOMotorCollection):
    obj = await collection.find_one({"_id": ObjectId(obj_id)})
    if obj:
        obj["_id"] = str(obj["_id"])
    return obj


async def get_obj_by_fields(query: dict, collection: AsyncIOMotorCollection) -> dict:
    if "_id" in query and isinstance(query["_id"], str):
        query["_id"] = ObjectId(query["_id"])

    obj = await collection.find_one(query)
    if obj:
        obj["_id"] = str(obj["_id"])
    return obj


async def create_obj(obj_data: dict, collection: AsyncIOMotorCollection):
    result = await collection.insert_one(obj_data)
    obj_id = str(result.inserted_id)
    obj = await collection.find_one({"_id": ObjectId(obj_id)})
    return obj


async def update_obj(obj_id: str, obj_data: dict, collection: AsyncIOMotorCollection):
    result = await collection.update_one(
        {"_id": ObjectId(obj_id)},
        {"$set": obj_data}
    )
    if result.matched_count > 0:
        obj_data["_id"] = obj_id
        return obj_data
    return None


async def delete_obj(obj_id: str, collection: AsyncIOMotorCollection):
    result = await collection.delete_one({"_id": ObjectId(obj_id)})
    if result.deleted_count > 0:
        return {"message": f"Object {obj_id} deleted successfully"}
    return {"error": "Object not found"}


async def latest_group_assignment(group_id: str, collection: AsyncIOMotorCollection) -> tuple:
    pipeline = [
        {"$match": {"group_id": group_id}},     # Фильтруем по group_id
        {"$sort": {"version": -1}},             # Сортируем по version в убывающем порядке
        {"$limit": 1},                          # Берем только первый результат после сортировки
    ]
    result = await collection.aggregate(pipeline).to_list(length=1)

    if result:
        # Return a tuple with assignment_id (_id) and max_version
        return result[0]["_id"], result[0]["version"]
    else:
        return None, 0



