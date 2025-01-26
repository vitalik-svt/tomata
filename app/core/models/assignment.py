import datetime as dt
from typing import Optional, List
from pydantic import ConfigDict, BaseModel, Field, model_validator
from pydantic.functional_validators import BeforeValidator

from typing_extensions import Annotated

from app.utils import load_json, load_yaml, get_event_type_mapper

# load user configs
event_type_mapper = get_event_type_mapper("app/configs/events.yaml")
assignment_default_data = load_yaml("app/configs/default_assignment.yaml", dt=dt)

# load form_schema schema for frontend js generator
form_schema = load_json(
    path="app/core/form_schema.json",
    event_type_mapper=list(event_type_mapper.keys()),
    event_description="""Событие должно срабатывать при ХХХ.
При срабатывании данного события должны передаваться следующие данные:"""
)


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

    @model_validator(mode="before")
    def set_default_event_data(cls, values):
        """Set data based on type by default"""
        event_type_ = values.get("event_type")
        if event_type_:
            values.setdefault("event_data", event_type_mapper[event_type_])
        return values


class Block(BaseModel):
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

    name: str
    author: Optional[str] = None
    description: Optional[str] = None
    created_at: str = Field(default=dt.datetime.now().isoformat())
    updated_at: str = Field(default=dt.datetime.now().isoformat())
    blocks: List[Block] = Field(default_factory=Block)


assignment_default = Assignment(**assignment_default_data)
