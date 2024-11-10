import os
from enum import Enum
import datetime as dt
from typing import Optional, List

from pydantic import ConfigDict, BaseModel, Field, EmailStr
from pydantic.functional_validators import BeforeValidator

from typing_extensions import Annotated

class EventType(str, Enum):
    ga_remove_from_shopping_list="GA:removeFromShoppingList"

class EventData(BaseModel):
    pass

class Image(BaseModel):
    image_path: str

class Event(BaseModel):
    type: EventType
    images: Optional[List[Image]]
    description: Optional[str] = None
    event_data: EventData

class Action(BaseModel):
    name: str
    description: Optional[str] = None
    events: List[Event] = Field(default_factory=list)

# Represents an ObjectId field in the database.
# It will be represented as a `str` on the model so that it can be serialized to JSON.
PyObjectId = Annotated[str, BeforeValidator(str)]

class Assignment(BaseModel):

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )

    assignment_name: str
    assignment_description: Optional[str] = None
    created_at: dt.datetime = Field(default_factory=dt.datetime.utcnow)
    updated_at: dt.datetime = Field(default_factory=dt.datetime.utcnow)
    author: str
    actions: List[Action] = Field(default_factory=list)


assignment_default = Assignment(
    **{
        "assignment_name": "New Assignment",
        "assignment_description": "Description",
        "author": "Author",
        "created_at": dt.datetime.utcnow(),
        "updated_at": dt.datetime.utcnow(),
        "actions": []
    }
)