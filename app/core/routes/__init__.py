from fastapi import APIRouter

from .general import router as general_router
from .assignment import router as assignment_router
from .user import router as user_router

core_router = APIRouter()

core_router.include_router(general_router)
core_router.include_router(assignment_router)
core_router.include_router(user_router)
