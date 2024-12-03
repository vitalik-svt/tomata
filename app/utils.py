from typing import Union
import os
import yaml
import json
from pathlib import Path
from jinja2 import Environment


def render_template(template: Union[dict, str], **template_vars) -> dict:
    if isinstance(template, dict):
        template_str = json.dumps(template)
    elif isinstance(template, str):
        template_str = template
    else:
        raise TypeError('template can be either dict or str')

    env = Environment()
    env.filters['tojson'] = json.dumps
    template_env = env.from_string(template_str)
    rendered_str = template_env.render(template_vars)
    render = json.loads(rendered_str)

    return render


def load_json(path, **template_vars) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        template_str = f.read()
        return render_template(template_str, **template_vars)


def load_yaml(path: str, **template_vars) -> dict:
    if os.path.exists(path) and Path(path).suffix in ('.yaml', 'yml'):
        with open(path, 'r') as f:
            template = yaml.safe_load(f)
            render = render_template(template, **template_vars)
        return render


def get_event_type_mapper(path) -> dict:
    event_type_mapper = {}
    event_type_mapper_raw = load_yaml(path).items()
    for event, params in event_type_mapper_raw:
        event_params = []
        for param in params:
            row = f"""'{param.get('key')}': '{param.get('value')}' {f'// {param.get('comment')}' if param.get('comment') else ''}"""
            event_params.append(row)
        event_type_mapper[event] = '\n'.join(event_params)

    return event_type_mapper


