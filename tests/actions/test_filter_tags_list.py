import pytest

from filter_openapi import filter_tags_list


@pytest.fixture
def sample_data():
    return {
        "tags": [
            {"name": "Pet", "description": "Everything about your Pets"},
            {"name": "Store", "description": "Access to Petstore orders"},
            {"name": "User", "description": "Operations about user"},
        ]
    }


def test_filter_tags_list(sample_data):
    allowed_tags = {"Pet", "User"}
    result = filter_tags_list(sample_data, allowed_tags)
    assert len(result["tags"]) == 2
    tag_names = {tag["name"] for tag in result["tags"]}
    assert tag_names == {"Pet", "User"}


def test_filter_tags_list_no_matches(sample_data):
    allowed_tags = {"None", "OfThese"}
    result = filter_tags_list(sample_data, allowed_tags)
    assert len(result["tags"]) == 0


def test_filter_tags_list_all_match(sample_data):
    allowed_tags = {"Pet", "Store", "User"}
    result = filter_tags_list(sample_data, allowed_tags)
    assert len(result["tags"]) == 3


def test_no_tags_in_data():
    data = {"info": {"title": "Test API"}}
    result = filter_tags_list(data.copy(), {"Pet"})
    assert result == data


def test_empty_tags_list():
    data = {"tags": []}
    result = filter_tags_list(data.copy(), {"Pet"})
    assert result == {"tags": []}


def test_allowed_tags_is_empty(sample_data):
    result = filter_tags_list(sample_data.copy(), set())
    assert len(result["tags"]) == 0
