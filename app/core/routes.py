import datetime as dt
from typing import List, Optional
from fastapi import APIRouter, FastAPI, HTTPException, Body, status, Depends
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection

from app.core.database import (get_collection,
                               create_assignment, get_assignment, update_assignment, delete_assignment)
from app.core.models import Assignment, assignment_to_js_schema, assignment_default, event_type_mapper

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def home_route(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@router.get("/assignments")
async def list_assignments_route(
        request: Request,
        collection: AsyncIOMotorCollection = Depends(get_collection)
    ):
    assignments = []
    async for assignment in collection.find().sort("created_at", -1):
        assignment["_id"] = str(assignment["_id"])  # Convert ObjectId to string
        assignments.append(assignment)
    return templates.TemplateResponse("list.html", {"request": request, "assignments": assignments})


@router.get("/assignment/new")
async def create_assignment_route(request: Request):
    assignment_data = assignment_default.dict(exclude_unset=True)
    return templates.TemplateResponse("edit.html", {
        "request": request,
        "assignment": assignment_data,
        "assignment_schema": assignment_to_js_schema(),
        "is_edit": False,
        "event_type_mapper": event_type_mapper
    })


@router.post("/assignment/new")
async def create_assignment_route(
    new_assignment: Assignment,
    collection: AsyncIOMotorCollection = Depends(get_collection)
):
    try:
        new_assignment_data = new_assignment.dict()
        result = await create_assignment(new_assignment_data, collection)
        assignment_id = str(result['_id'])
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating assignment: {e}")

    return JSONResponse(content={"id": assignment_id})  # we will redirect to get /assignment/{assignment_id} on frontend


@router.get("/assignment/{assignment_id}")
async def get_assignment_route(
    request: Request,
    assignment_id: str,
    collection: AsyncIOMotorCollection = Depends(get_collection)
):
    assignment = await get_assignment(assignment_id, collection)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return templates.TemplateResponse("edit.html", {
        "request": request,
        "assignment": assignment,
        "assignment_schema": assignment_to_js_schema(),
        "is_edit": bool(assignment_id),
        "event_type_mapper": event_type_mapper
    })


@router.post("/assignment/{assignment_id}")
async def save_assignment_route(
        assignment_id: str,
        updated_assignment: Assignment,
        collection: AsyncIOMotorCollection = Depends(get_collection)
    ):
    assignment = await get_assignment(assignment_id, collection)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    updated_assignment.updated_at = dt.datetime.now().isoformat()
    updated_data_dict = updated_assignment.dict(exclude_unset=True)
    await update_assignment(assignment_id, updated_data_dict, collection)
    return {**assignment, **updated_data_dict}


@router.delete("/assignment/{assignment_id}")
async def delete_assignment_route(
        assignment_id: str,
        collection: AsyncIOMotorCollection = Depends(get_collection)
    ):
    assignment = await get_assignment(assignment_id, collection)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    await delete_assignment(assignment_id, collection)
    return {"message": "Assignment deleted successfully"}


@router.post("/print")
async def print_route(request: Request, assignment: dict):  # Принимаем данные как dict
    return JSONResponse(content={"assignment_data": assignment})
