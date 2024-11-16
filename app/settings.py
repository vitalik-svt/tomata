import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    model_config = SettingsConfigDict(env_file='.env')

    # settings
    env: str = 'LOCAL'

    # app
    app_log_level: str = 'INFO'
    app_host: str = '0.0.0.0'
    app_port: int = 8000
    app_workers: int = 1
    app_reload: bool = True
    app_fastapi_middleware_secret_key: str = os.urandom(24)

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

