import pytest

from typing import List, Dict, Callable, Union
import asyncio

from app.core.services.assignment import async_recursive_apply, recursive_apply, clean_dict_field, get_image_from_loc


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