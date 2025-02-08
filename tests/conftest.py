import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="module")
def test_client():
    with TestClient(app) as client:
        yield client


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
