from typing import Optional
import datetime as dt
import logging

from passlib.context import CryptContext
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi import Request, Depends,  HTTPException
import jwt

from app.settings import settings
from app.core.models.user import User, UserInDB, Role
import app.core.services.database as db


logger = logging.getLogger(__name__)


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBasic()

SECRET_KEY = settings.app_jwt_secret_key
ALGORITHM = settings.app_jwt_algorithm


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


async def get_user(username: str) -> UserInDB | None:
    collection = await db.get_collection(collection_name=settings.app_users_collection)
    user_data = await db.get_obj_by_fields({'username': username}, collection)
    if user_data:
        return UserInDB(**user_data)
    else:
        return None


async def authenticate_user(username: str, password: str) -> UserInDB | None:
    user = await get_user(username)
    if user and verify_password(password, user.hashed_password):
        return user
    return None


async def get_authenticated_user(credentials: HTTPBasicCredentials = Depends(security)) -> UserInDB | None:
    user = await authenticate_user(credentials.username, credentials.password)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return user


def create_access_token(data: dict, expires_delta: int = 900):
    to_encode = data.copy()
    expire = dt.datetime.now() + dt.timedelta(seconds=expires_delta)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(request: Request) -> UserInDB | None:
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user = await get_user(username)

        if user and user.active:
            return user
        return None
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


async def require_authenticated_user(request: Request, current_user: Optional[UserInDB] = Depends(get_current_user)) -> UserInDB:
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return current_user


async def initialize_admin_user():
    """
    Check if any admin user exists in the MongoDB. If not, create one.
    """
    collection = await db.get_collection(
        db_name=settings.mongo_initdb_database,
        collection_name=settings.app_users_collection,
    )

    existing_admin = await db.get_obj_by_fields({"role": Role.admin.value}, collection)
    if not existing_admin:
        admin = User(
            username=settings.app_init_admin_username,
            hashed_password=get_password_hash(settings.app_init_admin_password),
            role=Role.admin.value
        )
        await db.create_obj(admin.model_dump(), collection)
        print("Admin user created successfully.")
    else:
        print("Admin user already exists.")

