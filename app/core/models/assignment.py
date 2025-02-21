from typing_extensions import Self
from typing import List, Dict, Union, Literal, Collection, Tuple, Any
import yaml
import json
import jsonref
from typing_extensions import Annotated
import datetime as dt
from pydantic import ConfigDict, BaseModel, Field, AliasChoices, model_validator
from pydantic.functional_validators import BeforeValidator
from pydantic.json_schema import SkipJsonSchema
from enum import Enum

from app.settings import settings


class EventData(BaseModel):
    key: str
    value: Union[str, int, float]
    comment: Union[str, None] = None


class EventsMapper(BaseModel):
    data: Dict[str, List[EventData]]

    @classmethod
    async def from_yaml(cls, path: str = settings.app_config_events_mapper_path) -> "EventsMapper":
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        return cls(data=data)

    def dump(self, return_str: bool = False) -> Union[Dict[str, str], str]:
        events_mapper = {}
        for event, params in self.data.items():
            event_params = []
            for param in params:
                event_params.append(f"""'{param.key}': '{param.value}' {f"// {param.comment}" if param.comment else ""}""")
            events_mapper[event] = '\n'.join(event_params)

        return json.dumps(events_mapper, indent=4, ensure_ascii=False) if return_str else events_mapper


class CustomBaseModel(BaseModel):

    @classmethod
    def update_json_schema_for_field(cls, field_name, data_to_update: Dict[str, Any]):
        """
        Method to update json_schema_extra for a particular field
        """
        if field_name in cls.model_fields:
            field = cls.model_fields[field_name]
            for key, value in data_to_update.items():
                field.json_schema_extra[key] = value

    @classmethod
    def _remove_keys_recursively(cls, d: dict | list, drop_keys: Collection) -> dict | list:

        if isinstance(d, dict):
            return {
                k: cls._remove_keys_recursively(v, drop_keys)
                for k, v in d.items()
                if k not in drop_keys
            }
        elif isinstance(d, list):
            return [
                cls._remove_keys_recursively(v, drop_keys) for v in d
            ]
        return d

    @classmethod
    def dump_schema(cls, mode: Literal['validation', 'serialization'] = 'serialization', return_str: bool = False, drop_keys: Union[Tuple, List] = ("$defs", "$ref")) -> Union[str, dict]:

        """
        Create schema for frontend generator https://github.com/json-editor/json-editor
        It's kinda looks like pydantic model_json_schema, but:
        - some needed for json-editor fields will be added in json_schema_extra
        - some unwanted for json-editor fields will be filtered here
        """

        schema_raw = cls.model_json_schema(mode=mode)
        schema_clean = jsonref.replace_refs(schema_raw).copy()

        # recursive delete
        schema_clean = cls._remove_keys_recursively(schema_clean, drop_keys)

        # drop class description comment from first level
        schema_clean.pop("description", None)  # Remove the description key if it exists

        return json.dumps(schema_clean, indent=4, ensure_ascii=False) if return_str else schema_clean


class Status(Enum):
    design = 'Design'
    review = 'Review'
    implementation = 'Implementation'
    works_on_dev = 'Works on dev'
    works_on_prod = 'Works on prod'


class Image(BaseModel):

    model_config = ConfigDict(
        json_schema_extra={"title": "Image", "type": "object", "format": "grid"}
    )

    # determine names explicitly as image_data, image_location, to not confuse with other keys
    # because we will iterate over whole Assignment/Document model and change them dynamically
    image_data: Union[str, SkipJsonSchema[None]] = Field(
        default=None,
        json_schema_extra={
            "title": "File",
            "type": "string",
            "media": {"binaryEncoding": "base64", "type": "img/png"},
            "options": {"grid_columns": 6, "multiple": True},
            "format": "url"
        }
    )
    image_location: Union[str, SkipJsonSchema[None]] = Field(
        default=None,
        json_schema_extra={"title": "location", "type": "string", "readonly": True}
    )
    image_description: Union[str, SkipJsonSchema[None]] = Field(
        default=None,
        json_schema_extra={"title": "Description", "type": "string", "options": {"grid_columns": 6}}
    )


class Event(CustomBaseModel):

    model_config = ConfigDict(
        json_schema_extra={"title": "Event", "type": "object"}
    )

    name: Union[str, SkipJsonSchema[None]] = Field(
        default=None,
        json_schema_extra={"title": "Event name", "type": "string", "minLength": 1, "propertyOrder": 100350}
    )
    images: Union[List[Image], SkipJsonSchema[None]] = Field(
        default=None,
        json_schema_extra={"title": "Images", "type": "array", "format": "table", "propertyOrder": 100400}
    )
    event_type: Union[str, SkipJsonSchema[None]] = Field(
        # will update enum only when need it (dynamically, later)
        default=None,
        json_schema_extra={"title": "Event Type", "type": "string", "enum": [], "propertyOrder": 100500}
    )
    description: Union[str, SkipJsonSchema[None]] = Field(
        default="Событие должно срабатывать при ХХХ\nПри срабатывании данного события должны передаваться следующие данные:",
        json_schema_extra={"title": "Event Description", "type": "string", "format": "xhtml", "options": {"wysiwyg": True}, "propertyOrder": 100600}
    )
    event_data: Union[str, SkipJsonSchema[None]] = Field(
        default=None,
        json_schema_extra={"title": "Event Data", "type": "string", "format": "xhtml", "options": {"wysiwyg": True}, "propertyOrder": 100700}
    )
    check_comment: Union[str, SkipJsonSchema[None]] = Field(
        default=None,
        json_schema_extra={"title": "Check comment", "type": "string", "format": "xhtml", "options": {"wysiwyg": True}, "propertyOrder": 100800}
    )
    check_images: Union[List[Image], SkipJsonSchema[None]] = Field(
        default_factory=list,
        json_schema_extra={"title": "Check Images", "type": "array", "format": "table", "propertyOrder": 100900}
    )
    internal_comment: Union[str, SkipJsonSchema[None]] = Field(
        default=None,
        json_schema_extra={"title": "Internal comment", "type": "string","format": "xhtml", "options": {"wysiwyg": True}, "propertyOrder": 101000}
    )
    event_ready: Union[bool, SkipJsonSchema[None]] = Field(
        default=False,
        json_schema_extra={"title": "Event ready", "type": "boolean", "format": "checkbox", "propertyOrder": 101100}
    )


class Block(BaseModel):

    model_config = ConfigDict(
        json_schema_extra={"title": "Block", "type": "object"}
    )

    name: Union[str, SkipJsonSchema[None]] = Field(
        default=None,
        json_schema_extra= {"title": "Block name","type": "string", "minLength": 1, "propertyOrder": 100100}
    )
    description: Union[str, SkipJsonSchema[None]] = Field(
        default=None,
        json_schema_extra={"title": "Block description", "format": "xhtml", "options": {"wysiwyg": True}, "propertyOrder": 100200}
    )
    block_comment: Union[str, SkipJsonSchema[None]] = Field(
        default=None,
        json_schema_extra={"title": "Block comment", "format": "xhtml", "options": {"wysiwyg": True}, "propertyOrder": 100201}
    )
    events: Union[List[Event], SkipJsonSchema[None]] = Field(
        default_factory=list,
        json_schema_extra={"title": "Block events", "type": "array", "propertyOrder": 100300}
    )


class AssignmentBase(CustomBaseModel):

    """
    ATTENTION, IN ANY CHANGE OF SCHEMA HERE OR IN UNDERLYING MODELS!

    1) NO SERIALIZATION ALIASES NOWHERE IN CHILD CLASSES EXCEPT _id!
    2) All added fields should be optional:
    add: "Union[required_type, SkipJsonSchema[None]]" just in case!
    3) All added fields should have default = None!

    NEW_FIELD: Union[str, SkipJsonSchema[None]] = Field(
        default=None,
        json_schema_extra={"title": ..., "type": ..., "propertyOrder": ...}
    )

    Here and everywhere in models:

    In case of renaming field:
    1) add previous name as validation_alias among with the new name!
    new_name: type = Field(..., validation_alias=AliasChoices('new_name', 'old_name'))

    In case of adding field:
    1) Make it Optional = None

    # useful docs
    https://docs.pydantic.dev/latest/concepts/json_schema/#programmatic-field-title-generation
    https://github.com/json-editor/json-editor
    """

    model_config = ConfigDict(
        use_enum_values=True,
        json_schema_extra={
            "title": "Technical Assignment"
        }
    )

    group_id: Union[str, SkipJsonSchema[None]] = Field(
        default=None,
        json_schema_extra={"title": "Group ID", "type": "string", "readonly": True, "propertyOrder": 10000}
    )
    name: Union[str, SkipJsonSchema[None]] = Field(
        default=None,
        json_schema_extra={"title": "Assignment Name", "type": "string", "minLength": 1, "propertyOrder": 10002}
    )
    status: Union[str, SkipJsonSchema[None]] = Field(
        default=Status.design.value,
        # will update enum only when need it
        json_schema_extra={"title": "Status", "type": "string", "enum": ['placeholder'], "propertyOrder": 100003}
    )
    issue: Union[str, SkipJsonSchema[None]] = Field(
        default=None,
        json_schema_extra={"title": "Issue number", "type": "string", "minLength": 1, "propertyOrder": 100004}
    )
    version: Union[int, SkipJsonSchema[None]] = Field(
        default=1,
        json_schema_extra={"title": "Version Number", "type": "integer", "readonly": True, "propertyOrder": 100005}
    )
    save_counter: Union[int, SkipJsonSchema[None]] = Field(
        default=0,
        json_schema_extra={"title": "Save Counter", "type": "integer", "readonly": True, "propertyOrder": 100006}
    )
    author: Union[str, SkipJsonSchema[None]] = Field(
        default=None,
        json_schema_extra={"title": "Author", "type": "string", "minLength": 1, "propertyOrder": 100020}
    )
    created_at: Union[str, SkipJsonSchema[None]] = Field(
        default=None,
        json_schema_extra={"title": "Create dtm", "type": "string", "readonly": True, "propertyOrder": 100030}
    )
    updated_at: Union[str, SkipJsonSchema[None]] = Field(
        default=None,
        json_schema_extra={"title": "Update dtm", "type": "string", "readonly": True, "propertyOrder": 100040}
    )
    description: Union[str, SkipJsonSchema[None]] = Field(
        default=None,
        json_schema_extra={"title": "Assignment description", "type": "string", "format": "markdown", "propertyOrder": 100050}
    )
    blocks: Union[List[Block], SkipJsonSchema[None]] = Field(
        default_factory=list,
        json_schema_extra={"title": "Blocks", "type": "array", "propertyOrder": 100060}
    )
    size_doc: Union[float, SkipJsonSchema[None]] = Field(
        default=0,
        validation_alias=AliasChoices('size_doc', ),
        json_schema_extra={"title": "Size doc, MB", "type": "float", "readonly": True, "propertyOrder": 101200}
    )
    size_total: Union[float, SkipJsonSchema[None]] = Field(
        default=0,
        validation_alias=AliasChoices('size_total', ),
        json_schema_extra={"title": "Size total, MB", "type": "float", "readonly": True, "propertyOrder": 101201}
    )


class AssignmentSchema(BaseModel):

    assignment_ui_schema: Union[str, SkipJsonSchema[None]] = Field(
        default=None,
        json_schema_extra={"title": "Assignment Schema", "type": "string", "readonly": True, "propertyOrder": 100102}
    )
    events_mapper: Union[str, SkipJsonSchema[None]] = Field(
        default=None,
        json_schema_extra={"title": "Events Mapper", "type": "string", "readonly": True, "propertyOrder": 100103}
    )


class AssignmentSchemaHash(BaseModel):

    assignment_ui_schema_hash: Union[str, SkipJsonSchema[None]] = Field(
        default=None,
        json_schema_extra={"title": "Assignment Schema Hash", "type": "string", "readonly": True, "propertyOrder": 101300}
    )


# Represents an ObjectId field in the database.
# It will be represented as a `str` on the model so that it can be serialized to JSON.
PyObjectId = Annotated[str, BeforeValidator(str)]


class AssignmentID(BaseModel):

    model_config = ConfigDict(
        populate_by_name=True,  # To work with "private" data _id -> id
    )

    id: Annotated[str, BeforeValidator(str)] = Field(..., validation_alias='_id', serialization_alias='id',
        json_schema_extra={"title": "Assignment ID", "type": "float", "readonly": True, "propertyOrder": 10001}
    )

    # overwriting standard method, careful!
    def model_dump(self, rename_mongo_id: bool = False, **kwargs):
        if rename_mongo_id:
            return super().model_dump(by_alias=False, **kwargs)
        else:
            return super().model_dump(by_alias=True, **kwargs)


class AssignmentInUI(AssignmentID, AssignmentSchemaHash, AssignmentBase):
    """
    Base + SchemaHash + ID
    """
    pass


class AssignmentWithFullSchema(AssignmentSchema, AssignmentSchemaHash, AssignmentBase):
    """
    Base + SchemaHash + Schema
    """
    pass


class AssignmentInDB(AssignmentID, AssignmentWithFullSchema):
    """
    Base + SchemaHash + Schema + ID
    """
    pass

