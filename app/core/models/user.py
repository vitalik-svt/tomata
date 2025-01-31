from typing import Annotated
from enum import Enum
from pydantic import BaseModel, Field
from pydantic.functional_validators import BeforeValidator


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class Role(Enum):
    admin: str = 'admin'
    editor: str = 'editor'
    viewer: str = 'viewer'


class User(BaseModel):
    username: str
    hashed_password: str
    role: str = Role.admin.value
    active: bool = True


PyObjectId = Annotated[str, BeforeValidator(str)]

class UserInDB(User):
    id: PyObjectId = Field(..., alias="_id")  # mongo id
