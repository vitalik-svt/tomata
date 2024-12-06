import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from base64 import b64encode


class Settings(BaseSettings):

    model_config = SettingsConfigDict(env_file='.env', env_prefix='AMTA_')

    # settings
    env: str = 'LOCAL'

    # app
    app_log_level: str = 'DEBUG'
    app_host: str = '0.0.0.0'
    app_port: int = 8000
    app_workers: int = 1
    app_reload: bool = True
    app_fastapi_middleware_secret_key: str = b64encode(os.urandom(24)).decode('utf-8')
    app_jwt_secret_key: str = b64encode(os.urandom(24)).decode('utf-8')
    app_jwt_algorithm: str = "HS256"
    app_jwt_token_sec: int = 86400

    app_assignments_collection: str = 'assignments'
    app_users_collection: str = 'users'
    app_init_admin_username: str = 'admin'
    app_init_admin_password: str = 'admin'

    # mongo
    mongo_server: str = 'mongo'
    mongo_port: int = 27017
    mongo_initdb_root_username: str = 'admin'
    mongo_initdb_root_password: str = 'admin'
    mongo_initdb_database: str = 'amta'
    mongodb_data_dir: str = './data/db'
    mongodb_log_dir: str = './log/mongodb'

    # mongo express
    me_config_basicauth_username: str = 'mexpress'
    me_config_basicauth_password: str = 'mexpress'
    me_config_http_port: int = 8071


settings = Settings()

