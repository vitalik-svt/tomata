import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from bson import ObjectId

from app.main import app


@pytest.fixture(scope="module")
def test_client():
    with TestClient(app) as client:
        yield client


@pytest.fixture
def mock_s3():
    mock = AsyncMock()
    mock.s3_to_base64_image.return_value = "base64_image_string"
    mock.base64_image_to_s3.return_value = "s3://bucket/prefix/file_key"
    return mock

@pytest.fixture
def mock_db():
    mock = AsyncMock()
    mock.find_one.return_value = {"_id": ObjectId('507f1f77bcf86cd799439011'), "name": "assignment1", "status": "active"}
    mock.get_obj_by_id.return_value = {"_id": ObjectId('507f1f77bcf86cd799439011'), "name": "assignment1", "status": "active"}
    mock.update_obj.return_value = {"_id": ObjectId('507f1f77bcf86cd799439011'), "status": "updated"}
    return mock

@pytest.fixture
def mock_utils():
    mock = MagicMock()
    mock.format_date.return_value = "2025-02-09"
    mock.get_model_size.return_value = 1024
    mock.get_hash.return_value = "hash_value"
    return mock

@pytest.fixture()
def mock_collection():
    return AsyncMock()


@pytest.fixture()
def mock_db_collection_dependency(mock_collection):
    async def mock_dependency(*args, **kwargs):
        return mock_collection
    return mock_dependency


@pytest.fixture()
def get_full_assignment():
    return {
    "_id": "67a72006a08815331075b43d",
    "group_id": "6b8a5720e38b482c995c46e377cd6aea",
    "name": "000",
    "status": "Design",
    "issue": "LM-1793",
    "version": 1,
    "save_counter": 2,
    "author": "admin",
    "created_at": "2025-02-08T09:12:38.491199",
    "updated_at": "2025-02-08T10:07:35.687287",
    "description": "ОЧЕНЬ ВАЖНО!!!",
    "blocks": [
        {
            "block_comment": "",
            "description": "",
            "events": [
                {
                    "check_comment": "",
                    "check_images": [
                        {
                            "description": "",
                            "image_data": "data:image/jpeg;base64,/9j/4cbVRX....0AKgAAAAgAW",
                            "image_location": "s3://bucket_name/path/to/file/filename1.png"
                        },
                        {
                            "description": "",
                            "image_data": "data:image/jpeg;base64,/9j/4aJ8RX....hpZgAATU0",
                            "image_location": "s3://bucket_name/path/to/file/filename1.png"
                        },
                    ],
                    "description": "Событие должно срабатывать при ХХХ",
                    "event_data": "'elementType': 'page' \n'elementBlock': 'productDetail' // блок, в котором расположен элемент",
                    "event_ready": False,
                    "event_type": "GA:detail",
                    "images": [
                        {
                            "description": "",
                            "image_data": "data:image/jpeg;base64,/9j/4cbVRX....0AKgAAAAgAW",
                            "image_location": "s3://bucket_name/path/to/file/filename1.png"
                        },
                        {
                            "description": "",
                            "image_data": "data:image/jpeg;base64,/9j/4aJ8RX....hpZgAATU0",
                            "image_location": "s3://bucket_name/path/to/file/filename1.png"
                        },
                        {
                            "description": "",
                            "image_data": "data:image/jpeg;base64,/9j/4aJ8RX....hpZgAATU0",
                            "image_location": "s3://bucket_name/path/to/file/filename1.png"
                        }
                    ],
                    "internal_comment": "",
                    "name": ""
                }
            ],
            "name": ""
        }
    ],
    "size": 2.24,
    "assignment_ui_schema_hash": "PLACEHOLDER",
    "assignment_ui_schema": "PLACEHOLDER",
    "events_mapper": "PLACEHOLDER"
}


@pytest.fixture()
def get_image_assignment():
    return {
    "_id": "67a72006a08815331075b43d",
    "blocks": [
        {
            "events": [
                {
                    "check_images": [
                        {
                            "description": "",
                            "image_data": "data:image/jpeg;base64,/9j/4cbVRX....0AKgAAAAgAW",
                            "image_location": "s3://bucket_name/path/to/file/filename1.png"
                        },
                        {
                            "description": "",
                            "image_data": "data:image/jpeg;base64,/9j/4aJ8RX....hpZgAATU0",
                            "image_location": "s3://bucket_name/path/to/file/filename2.png"
                        },
                    ],
                    "description": "Событие должно срабатывать при ХХХ",
                    "images": [
                        {
                            "description": "",
                            "image_data": "data:image/jpeg;base64,/9j/4cbVRX....0AKgAAAAgAW",
                            "image_location": "s3://bucket_name/path/to/file/filename3.png"
                        },
                        {
                            "description": "",
                            "image_data": "data:image/jpeg;base64,/9j/4aJ8RX....hpZgAATU0",
                            "image_location": "s3://bucket_name/path/to/file/filename4.png"
                        }
                    ],
                }
            ],
        }
    ]
}
