from typing import Any
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from bson import ObjectId
from app.settings import settings

MONGO_URI = f"mongodb://{settings.mongo_initdb_root_username}:{settings.mongo_initdb_root_password}@{settings.mongo_server}:{settings.mongo_port}/{settings.mongo_initdb_database}?authSource=admin"
ASSIGMENTS_COLLECTION = 'assignments'


async def get_db(db_name: str = settings.mongo_initdb_database) -> AsyncIOMotorClient:
    client = AsyncIOMotorClient(MONGO_URI)
    return client[db_name]


async def get_collection(collection_name: str = ASSIGMENTS_COLLECTION) -> AsyncIOMotorCollection:
    db = await get_db()
    return db[collection_name]


async def get_assignment(assignment_id: str, collection: AsyncIOMotorCollection):
    assignment = await collection.find_one({"_id": ObjectId(assignment_id)})
    if assignment:
        assignment["_id"] = str(assignment["_id"])
    return assignment


async def create_assignment(assignment_data: dict, collection: AsyncIOMotorCollection):
    result = await collection.insert_one(assignment_data)
    assignment_id = str(result.inserted_id)
    assignment = await collection.find_one({"_id": ObjectId(assignment_id)})
    return assignment


async def update_assignment(assignment_id: str, assignment_data: dict, collection: AsyncIOMotorCollection):
    result = await collection.update_one(
        {"_id": ObjectId(assignment_id)},
        {"$set": assignment_data}
    )
    if result.matched_count > 0:
        assignment_data["_id"] = assignment_id
        return assignment_data
    return None


async def delete_assignment(assignment_id: str, collection: AsyncIOMotorCollection):
    result = await collection.delete_one({"_id": ObjectId(assignment_id)})
    if result.deleted_count > 0:
        return {"message": f"Assignment {assignment_id} deleted successfully"}
    return {"error": "Assignment not found"}

