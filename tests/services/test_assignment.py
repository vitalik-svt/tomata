import pytest
from bson import ObjectId

from app.core.services.assignment import (
    async_recursive_apply, recursive_apply, clean_dict_field, get_assignment_data,
    duplicate_assignment, get_all_assignments_data, group_assignments_data
)

def test_recursive_apply(mock_utils):
    data = {
        "image_location": "some_url",
        "details": {
            "image_location": "another_url",
            "name": "Assignment1"
        }
    }

    def operation(value, **kwargs):
        return value.upper()

    target_keys = ["image_location"]
    result = recursive_apply(data, target_keys, operation)

    assert result["image_location"] == "SOME_URL"
    assert result["details"]["image_location"] == "ANOTHER_URL"


@pytest.mark.asyncio
async def test_async_recursive_apply(mock_utils):
    data = {
        "image_location": "some_url",
        "details": {
            "image_location": "another_url",
            "name": "Assignment1"
        }
    }

    async def async_operation(value, **kwargs):
        return value.upper()

    target_keys = ["image_location"]
    result = await async_recursive_apply(data, target_keys, async_operation)

    assert result["image_location"] == "SOME_URL"
    assert result["details"]["image_location"] == "ANOTHER_URL"


def test_clean_data():
    data = {'foo': 'bar'}
    assert clean_dict_field(data, 'foo') == {'foo': ''}


def test_clean_assignment_images():
    data = {
        'images': [
            {'image_location': 'foo', 'image_data': 'bar', 'description': 'baz'},
            {'image_location': 'foo1', 'image_data': 'bar1', 'description': 'baz1'}
        ]
    }
    result = recursive_apply(
        data=data,
        target_keys=['images'],
        operation=clean_dict_field,
        operation_kwargs={"field_to_clean": 'image_data'})
    assert result == {
        'images': [
            {'image_location': 'foo', 'image_data': '', 'description': 'baz'},
            {'image_location': 'foo1', 'image_data': '', 'description': 'baz1'}
        ]
    }


def test_load_images_to_assignment():

    def get_image_from_loc_(image_data, image_loc_field, image_data_field) -> dict:
        if image_data.get(image_loc_field) and len(image_data.get(image_loc_field)) > 0:
            image_data[image_data_field] = f"got data_from loc: {image_data.get(image_loc_field)}"
        return image_data

    data = {
        'name': '',
        'blocks': [
            {
                'name': 'block1',
                'images': [
                    {'image_location': 'foo', 'image_data': 'bar', 'description': 'baz'},
                    {'image_location': 'foo1', 'image_data': 'bar1', 'description': 'baz1'}
                ]
            }
        ],
        'images': [
            {'image_location': 'foo', 'image_data': 'bar', 'description': 'baz'},
            {'image_location': 'foo1', 'image_data': 'bar1', 'description': 'baz1'}
        ]
    }

    result = recursive_apply(
        data=data,
        target_keys=['images'],
        operation=get_image_from_loc_,
        operation_kwargs={"image_loc_field": 'image_location', "image_data_field": 'image_data'}
    )
    assert result == {
        'name': '',
        'blocks': [
            {
                'name': 'block1',
                'images': [
                    {'image_location': 'foo', 'image_data': 'got data_from loc: foo', 'description': 'baz'},
                    {'image_location': 'foo1', 'image_data': 'got data_from loc: foo1', 'description': 'baz1'}
                ]
            }
        ],
        'images': [
            {'image_location': 'foo', 'image_data': 'got data_from loc: foo', 'description': 'baz'},
            {'image_location': 'foo1', 'image_data': 'got data_from loc: foo1', 'description': 'baz1'}
        ]
    }


async def multiply_by_2(x):
    return x * 2


@pytest.mark.asyncio
async def test_multiply_list_of_numbers():
    data = {
        'numbers': [1, 2, 3]
    }
    result = await async_recursive_apply(
        data, 'numbers', multiply_by_2)
    assert result == {
        'numbers': [2, 4, 6]
    }

@pytest.mark.asyncio
async def test_multiply_in_nested_dict():
    data = {
        'data': {
            'numbers': [1, 2, 3]
        },
        'other_data': {
            'nested_numbers': [4, 5]
        }
    }
    result = await async_recursive_apply(data, 'numbers', multiply_by_2)
    assert result == {
        'data': {
            'numbers': [2, 4, 6]
        },
        'other_data': {
            'nested_numbers': [4, 5]
        }
    }


@pytest.mark.asyncio
async def test_multiply_in_list_of_dicts():
    data = [
        {
            'numbers': [1, 2, 3]
        },
        {
            'other_data': {
                'nested_numbers': [4, 5]
            }
        }
    ]
    result = await async_recursive_apply(data, 'numbers', multiply_by_2)
    assert result == [
        {
            'numbers': [2, 4, 6]
        },
        {
            'other_data':
                {
                    'nested_numbers': [4, 5]
                }
        }
    ]


@pytest.mark.asyncio
async def test_no_target_key():
    data = {
        'other_data': {'nested_numbers': [4, 5]}
    }
    result = await async_recursive_apply(data, 'numbers', multiply_by_2)
    assert result == {
        'other_data': {'nested_numbers': [4, 5]}
    }


# Test case 5: Empty dictionary or list should remain unchanged
@pytest.mark.asyncio
async def test_empty_data():
    data_empty_dict = {}
    data_empty_list = []
    result_empty_dict = await async_recursive_apply(data_empty_dict, 'numbers', multiply_by_2)
    result_empty_list = await async_recursive_apply(data_empty_list, 'numbers', multiply_by_2)
    assert result_empty_dict == {}
    assert result_empty_list == []


@pytest.mark.asyncio
async def test_get_assignment_data(mock_db):
    assignment_id = '507f1f77bcf86cd799439011'
    collection = mock_db

    result = await get_assignment_data(assignment_id, collection)

    assert result["name"] == "assignment1"
    assert result["status"] == "active"


def test_group_assignments_data():
    assignments = [
        {"group_id": "group1", "name": "assignment1", "updated_at": "2024-01-01", "created_at": "2024-01-01"},
        {"group_id": "group1", "name": "assignment2", "updated_at": "2024-01-01", "created_at": "2024-01-01"},
        {"group_id": "group2", "name": "assignment3", "updated_at": "2024-01-01", "created_at": "2024-01-01"}
    ]

    result = group_assignments_data(assignments)

    assert len(result) == 2
    assert "group1" in result
    assert len(result["group1"]["assignments"]) == 2