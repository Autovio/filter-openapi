import pytest

from filter_openapi import filter_paths_by_tags


@pytest.fixture
def sample_data():
    return {
        "paths": {
            "/pet": {
                "post": {
                    "tags": ["pet"],
                    "summary": "Add a new pet to the store",
                },
                "put": {
                    "tags": ["pet"],
                    "summary": "Update an existing pet",
                },
            },
            "/pet/findByStatus": {
                "get": {
                    "tags": ["pet"],
                    "summary": "Finds Pets by status",
                }
            },
            "/store/order": {
                "post": {
                    "tags": ["store"],
                    "summary": "Place an order for a pet",
                }
            },
            "/user/createWithList": {
                "post": {
                    "tags": ["user"],
                    "summary": "Creates list of users with given input array",
                }
            },
            "/mixed/tags": {
                "get": {"tags": ["pet", "user"], "summary": "Mixed tags"},
                "post": {"tags": ["store"], "summary": "Store only"},
            },
            "/no/tags": {"get": {"summary": "No tags here"}},
        }
    }


def test_filter_paths_by_pet_tag(sample_data):
    allowed_tags = {"pet"}
    result = filter_paths_by_tags(sample_data, allowed_tags)

    kept_paths = result["paths"]
    assert "/pet" in kept_paths
    assert "/pet/findByStatus" in kept_paths
    assert "/store/order" not in kept_paths
    assert "/user/createWithList" not in kept_paths
    assert "/mixed/tags" in kept_paths
    assert "get" in kept_paths["/mixed/tags"]
    assert "post" not in kept_paths["/mixed/tags"]
    assert "/no/tags" not in kept_paths


def test_filter_paths_by_store_tag(sample_data):
    allowed_tags = {"store"}
    result = filter_paths_by_tags(sample_data, allowed_tags)

    kept_paths = result["paths"]
    assert "/pet" not in kept_paths
    assert "/pet/findByStatus" not in kept_paths
    assert "/store/order" in kept_paths
    assert "/user/createWithList" not in kept_paths
    assert "/mixed/tags" in kept_paths
    assert "get" not in kept_paths["/mixed/tags"]
    assert "post" in kept_paths["/mixed/tags"]


def test_filter_paths_multiple_tags(sample_data):
    allowed_tags = {"pet", "user"}
    result = filter_paths_by_tags(sample_data, allowed_tags)

    kept_paths = result["paths"]
    assert "/pet" in kept_paths
    assert "post" in kept_paths["/pet"]
    assert "put" in kept_paths["/pet"]
    assert "/pet/findByStatus" in kept_paths
    assert "/store/order" not in kept_paths
    assert "/user/createWithList" in kept_paths
    assert "/mixed/tags" in kept_paths
    assert "get" in kept_paths["/mixed/tags"]
    assert "post" not in kept_paths["/mixed/tags"]


def test_filter_paths_no_matching_tags(sample_data):
    allowed_tags = {"nonexistent"}
    result = filter_paths_by_tags(sample_data, allowed_tags)
    assert not result["paths"]


def test_data_without_paths_key():
    data = {"info": {"title": "Test"}}
    result = filter_paths_by_tags(data, {"pet"})
    assert "paths" not in result


def test_paths_is_empty():
    data = {"paths": {}}
    result = filter_paths_by_tags(data, {"pet"})
    assert not result["paths"]


def test_operation_without_tags_field(sample_data):
    allowed_tags = {"pet"}
    # The operation in "/no/tags" has no "tags" field
    result = filter_paths_by_tags(sample_data, allowed_tags)
    assert "/no/tags" not in result["paths"]


def test_keep_operation_ids_in_addition_to_tags():
    data = {
        "paths": {
            "/pet": {"get": {"tags": ["pet"], "operationId": "getPet"}},
            "/store": {
                "get": {"tags": ["store"], "operationId": "getStore"},
                "post": {"tags": ["store"], "operationId": "createStore"},
            },
            "/user": {"get": {"tags": ["user"], "operationId": "getUser"}},
            "/no/tags": {"get": {"operationId": "noTags"}},
        }
    }
    result = filter_paths_by_tags(data, {"pet"}, {"getStore", "noTags"})

    kept_paths = result["paths"]
    assert "get" in kept_paths["/pet"]
    assert list(kept_paths["/store"]) == ["get"]
    assert "/user" not in kept_paths
    assert "get" in kept_paths["/no/tags"]
