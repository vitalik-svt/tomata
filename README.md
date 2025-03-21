# TOMATA

Tool for creation/management and Document sharing.<br>
Lets you create, store and view Document in particular format.<br>
Provides role model, multiple independent versions of document.<br>
Can handle document schema change.<br>

## Run

1. create `.env` from `.env.template` and set envs
2. run `docker-compose up -d` for full run (with database)

## Test

1. `poetry shell`
2. `pytest`

## Development

FastApi, MongoDB (for documents), Minio S3 (for images), [Json-editor](https://github.com/json-editor/json-editor) (Plain JS for UI form creation)<br>
Document (here and everywhere: Document === Assignment) model based on Pydantic.
With additional fields, for Json-editor.<br>
Model can be changed: that will lead to creation of new schema version.<br>
Schema - it's basically tree of Pydantic models.
