import datetime as dt
from typing import Optional, List
from pydantic import ConfigDict, BaseModel, Field, model_validator, validator, field_validator
from pydantic.functional_validators import BeforeValidator
from enum import Enum
from bson import ObjectId

from typing_extensions import Annotated


class Status(Enum):
    design = 'Design'
    review = 'Review'
    implementation = 'Implementation'
    discussion = 'Discussion'
    works_on_dev = 'Works on dev'
    works_on_prod = 'Works on prod'


class Image(BaseModel):
    file: str
    description: str


class Event(BaseModel):
    name: str
    event_type: Optional[str]
    description: Optional[str]
    images: Optional[List[Image]]
    event_data: str
    check_comment: str
    check_images: Optional[List[Image]]
    internal_comment: str
    event_ready: bool


class Block(BaseModel):
    name: str
    description: Optional[str] = None
    events: List[Event] = Field(default_factory=list)


class AssignmentNew(BaseModel):

    model_config = ConfigDict(
        use_enum_values=True
    )

    assignment_schema: str
    events_mapper: str
    name: str  # can be changed
    status: Optional[str] = None
    issue: Optional[str] = None
    group_id: Optional[str] = None
    weight_mb: Optional[float] = 0
    version: int = 1
    save_counter: int = 0
    author: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[str] = Field(default=dt.datetime.now().isoformat())
    updated_at: Optional[str] = Field(default=dt.datetime.now().isoformat())
    blocks: List[Block] = Field(default_factory=Block)


# Represents an ObjectId field in the database.
# It will be represented as a `str` on the model so that it can be serialized to JSON.
PyObjectId = Annotated[str, BeforeValidator(str)]


class AssignmentInDB(AssignmentNew):
    model_config = ConfigDict(
        populate_by_name=True,  # to have "private" data like "_id"
        arbitrary_types_allowed=True
    )

    id: PyObjectId = Field(..., alias="_id")  # mongo id
