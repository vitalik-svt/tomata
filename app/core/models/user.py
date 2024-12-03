from pydantic import BaseModel
from enum import Enum


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class Role(Enum):
    admin: str = 'admin'


class User(BaseModel):
    username: str
    role: str = Role.admin.value


class UserInDB(User):
    hashed_password: str


class UserCreate(BaseModel):
    username: str
    password: str
    role: Role
