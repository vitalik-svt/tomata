import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from base64 import b64encode
from pathlib import Path


class Settings(BaseSettings):

    model_config = SettingsConfigDict(env_file='.env', env_prefix='TOMATA_')

    # settings
    env: str = 'LOCAL'

    # app
    app_log_level: str = 'DEBUG'
    app_log_folder: str = './logs'
    app_host: str = '0.0.0.0'
    app_port: int = 8000
    app_workers: int = 1
    app_reload: bool = True
    app_fastapi_middleware_secret_key: str = b64encode(os.urandom(24)).decode('utf-8')
    app_jwt_secret_key: str = b64encode(os.urandom(24)).decode('utf-8')
    app_jwt_algorithm: str = 'HS256'
    app_jwt_token_sec: int = 86400

    app_assignments_collection: str = 'assignments'
    app_users_collection: str = 'users'

    app_config_events_mapper_path: str = 'app/configs/events_mapper.yaml'

    app_init_admin_username: str = 'admin'
    app_init_admin_password: str = 'admin'

    # mongo
    mongo_server: str = 'mongo'
    mongo_port: int = 27017
    mongo_initdb_root_username: str = 'admin'
    mongo_initdb_root_password: str = 'admin'
    mongo_initdb_database: str = 'tomata'
    mongodb_data_dir: str = './data/db'
    mongodb_log_dir: str = './log/mongodb'

    # mongo express
    me_config_basicauth_username: str = 'mexpress'
    me_config_basicauth_password: str = 'mexpress'
    me_config_http_port: int = 8071

    # minio
    s3_server: str = 'minio'
    s3_port: int = 9000
    minio_ui_port: int = 9001
    s3_access_key_id: str = 'minio'
    s3_secret_access_key: str = 'minio123'
    s3_images_bucket: str = 'images'

    @property
    def mongo_uri(self):
        return f"mongodb://{self.mongo_initdb_root_username}:{self.mongo_initdb_root_password}@{self.mongo_server}:{self.mongo_port}/{self.mongo_initdb_database}?authSource=admin"

    @property
    def s3_endpoint(self):
        return f'http://{self.s3_server}:{self.s3_port}'

    @property
    def app_log_path(self):
        return Path(self.app_log_folder)


settings = Settings()

