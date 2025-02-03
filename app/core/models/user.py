from typing import Annotated
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
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

    model_config = ConfigDict(
        populate_by_name=True,  # to have "private" data like "_id"
    )

    id: PyObjectId = Field(..., validation_alias='_id', serialization_alias='id')

    def model_dump(self, rename_mongo_id: bool = False, **kwargs):
        if rename_mongo_id:
            return super().model_dump(by_alias=False, **kwargs)
        else:
            return super().model_dump(by_alias=True, **kwargs)