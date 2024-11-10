import os
from enum import Enum
import datetime as dt
from typing import Optional, List, Dict
from pydantic import ConfigDict, BaseModel, Field, EmailStr, model_validator
from pydantic.functional_validators import BeforeValidator

from typing_extensions import Annotated


class EventType(str, Enum):
    ga_remove_from_shopping_list = "GA:removeFromShoppingList"
    ga_promo_click = "GA:promoClick"

    default_event_data = {
        "GA:removeFromShoppingList": {
            "action": "remove",
            "item_type": "shopping_list",
            "source": "GA"
        },
        "GA:promoClick": {
            "action": "click",
            "promotion": "promo",
            "source": "GA"
        }
    }

    @classmethod
    def get_default_event_data(cls, event_type: "EventType") -> Dict[str, Optional[str]]:
        return cls.default_event_data.get(event_type.value, {}).copy()

class Image(BaseModel):
    image_path: str

class Event(BaseModel):
    type: EventType
    images: Optional[List[Image]]
    description: Optional[str] = None
    event_data: Dict[str, Optional[str]] = Field(default_factory=dict)

    @model_validator(mode="before")
    def set_default_event_data(cls, values):
        """Set data based on type by default"""
        event_type = values.get("type")
        if event_type:
            values.setdefault("event_data", EventType.get_default_event_data(event_type))
        return values


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