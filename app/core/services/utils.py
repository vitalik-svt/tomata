from typing import Union, Any
import os
import sys

import pydantic
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


def load_yaml(path: str, **template_vars) -> Any:
    if os.path.exists(path) and Path(path).suffix in ('.yaml', 'yml'):
        with open(path, 'r') as f:
            template = yaml.safe_load(f)
            render = render_template(template, **template_vars)
        return render


def get_model_size(data: pydantic.BaseModel | dict | Any) -> float:

    """
    :return: size in Mbytes
    """

    if isinstance(data, pydantic.BaseModel):
        data = json.dumps(data.model_dump())
    elif isinstance(data, dict):
        data = json.dumps(data)
    else:
        pass

    return round(sys.getsizeof(data) / (1024 ** 2), 2)
