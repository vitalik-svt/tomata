import pytest

from app.core.models.assignment import EventData, EventsMapper, Event, Image, AssignmentBase, Block, Status
from app.settings import settings


# 1. Test EventData Model
def test_event_data_model():
    event_data = EventData(key="key1", value="value1")
    assert event_data.key == "key1"
    assert event_data.value == "value1"
    assert event_data.comment is None

    # Test with comment
    event_data_with_comment = EventData(key="key2", value="value2", comment="Test comment")
    assert event_data_with_comment.comment == "Test comment"


# 2. Test EventsMapper Model
@pytest.mark.asyncio
async def test_events_mapper_from_yaml():
    events_mapper = await EventsMapper.from_yaml(path=settings.app_config_events_mapper_path)
    assert isinstance(events_mapper, EventsMapper)


def test_dump_method():
    events_mapper = EventsMapper(data={"event_name": [EventData(key="key1", value="value1")]})
    result = events_mapper.dump(return_str=True)
    assert isinstance(result, str)
    assert "key1" in result


# 3. Test CustomBaseModel Methods
def test_update_json_schema_for_field():
    # Test that the schema is updated
    data_to_update = {"example_key": "example_value"}
    AssignmentBase.update_json_schema_for_field("name", data_to_update)
    field = AssignmentBase.model_fields["name"]
    assert "example_key" in field.json_schema_extra
    assert field.json_schema_extra["example_key"] == "example_value"


def test_remove_keys_recursively():
    data = {"key1": {"key_to_drop_1": "value", "key_to_drop_2": ["value", "value2"]}, "key2": "value2"}
    result = AssignmentBase._remove_keys_recursively(data, drop_keys=("key_to_drop_1", "key_to_drop_2"))
    assert "key1" in result
    assert "key2" in result
    assert result == {"key1": {}, "key2": "value2"}


# 4. Test Event Model
def test_event_model():
    event = Event(name="Test Event", description="This is a test event", event_data="Some data")
    assert event.name == "Test Event"
    assert event.description == "This is a test event"
    assert event.event_data == "Some data"


# 5. Test Image Model
def test_image_model():
    image = Image(image_data="data", image_location="location", image_description="Test image")
    assert image.image_data == "data"
    assert image.image_location == "location"
    assert image.image_description == "Test image"


# 6. Test AssignmentBase Model
def test_assignment_base_model():
    assignment = AssignmentBase(
        group_id="group1",
        name="Assignment 1",
        status=Status.design.value,
        issue="ISSUE123",
        version=1,
        description="Test description"
    )
    assert assignment.group_id == "group1"
    assert assignment.name == "Assignment 1"
    assert assignment.status == Status.design.value
    assert assignment.issue == "ISSUE123"


# 7. Test Block Model
def test_block_model():
    block = Block(
        name="Block 1",
        description="Test block",
        events=[Event(name="Event1", description="Event 1", event_data="data")]
    )
    assert block.name == "Block 1"
    assert block.description == "Test block"
    assert len(block.events) > 0
    assert block.events[0].name == "Event1"

