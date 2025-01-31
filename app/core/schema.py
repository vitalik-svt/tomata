import json
from typing import Optional

from app.settings import settings
from app.utils import load_json, load_yaml
from app.core.models.assignment import Status


def get_events_mapper(
        path: str = settings.app_config_events_mapper_path,
) -> str | dict:

    events_mapper = {}
    events_mapper_raw = load_yaml(path).items()
    for event, params in events_mapper_raw:
        event_params = []
        for param in params:
            row = f"""'{param.get('key')}': '{param.get('value')}' {f'// {param.get('comment')}' if param.get('comment') else ''}"""
            event_params.append(row)
        events_mapper[event] = '\n'.join(event_params)

    return events_mapper


def get_assignment_schema(
        path: str = settings.app_config_assignment_schema_path,
        status: Optional[list] = None,
        events_types: Optional[list] = None
) -> str | dict:

    if not status:
        status = [status.value for status in Status]

    if not events_types:
        events_mapper = get_events_mapper()
        events_types = list(events_mapper.keys())

    assignment_schema = load_json(
        path=path,
        status=status,
        events_types=events_types,
        event_description="""Событие должно срабатывать при ХХХ.
При срабатывании данного события должны передаваться следующие данные:"""
    )

    return assignment_schema
