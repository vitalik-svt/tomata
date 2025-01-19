# TOMATA

Automated technical assignment tool.<br>
Lets you create, store and print Technical Assignments in particular format.<br>
Convenient, if all yours assignment are in particular structure, and consists of same elements.

## User modifications

1. **List of events and event_data** <br>
   You can change it in `app/config/events.yaml`. `key`, `value` are mandatory, `comment` optional.
2. **Default assignment** <br>
   That creates by default, can be changed in `app/config/default_assignment.yaml`
3. **Default values** for new parts of Assignment <br>
   Can be changed in pydantic models `app/core/models.py`

After any modification, app should be restarted:
- `docker-compose down`
- `docker-compose up -d`

## Development

1. create `.env` from `.env.template` and set envs
2. run `docker-compose up -d` for full run (with database)
3. run `poetry run python script.py` for app only (without database)

## Info

Form creation based on: https://github.com/json-editor/json-editor
