from typing import Literal
from app.core.models.assignment import Event, EventsMapper, AssignmentInUI, Status


async def get_actual_schema_data(
        assignment_class_name: str = Literal['AssignmentInUI', 'AssignmentInDB', 'AssignmentWithSchema', 'AssignmentBase']
) -> tuple[str, str]:
    """
    Updating all json descriptions (because it's base for Json Form creation) with most actual data
    Getting Schema and Events mapper (both in json string) to pass it to Front
    """

    Event.update_json_schema_for_field('event_type', {"enum": list((await EventsMapper.from_yaml()).dump().keys())})
    eval(assignment_class_name).update_json_schema_for_field('status', {"enum": [status.value for status in Status]})

    assignment_ui_schema = eval(assignment_class_name).dump_schema(return_str=True)
    events_mapper = (await EventsMapper.from_yaml()).dump(return_str=True)

    return assignment_ui_schema, events_mapper
