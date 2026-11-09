import pytest

from filter_openapi import Method, filter_endpoint


@pytest.fixture
def sample_data():
    return {
        "paths": {
            "/pet/{petId}": {
                "get": {"summary": "Find pet by ID"},
                "post": {"summary": "Updates a pet in the store with form data"},
                "delete": {"summary": "Deletes a pet"},
            },
            "/pet/findByStatus": {"get": {"summary": "Finds Pets by status"}},
        }
    }


def test_filter_endpoint_keep_get(sample_data):
    methods_to_keep = [Method.GET]
    result = filter_endpoint(sample_data, "/pet/{petId}", methods_to_keep)

    path_item = result["paths"]["/pet/{petId}"]
    assert "get" in path_item
    assert "post" not in path_item
    assert "delete" not in path_item


def test_filter_endpoint_keep_multiple_methods(sample_data):
    methods_to_keep = [Method.GET, Method.DELETE]
    result = filter_endpoint(sample_data, "/pet/{petId}", methods_to_keep)

    path_item = result["paths"]["/pet/{petId}"]
    assert "get" in path_item
    assert "post" not in path_item
    assert "delete" in path_item


def test_filter_endpoint_remove_path_if_no_methods_left(sample_data):
    methods_to_keep = []
    result = filter_endpoint(sample_data, "/pet/{petId}", methods_to_keep)
    assert "/pet/{petId}" not in result["paths"]


def test_filter_endpoint_remove_single_method_path(sample_data):
    methods_to_keep = []
    result = filter_endpoint(sample_data, "/pet/findByStatus", methods_to_keep)
    assert "/pet/findByStatus" not in result["paths"]


def test_filter_endpoint_path_not_found(sample_data):
    original_data_str = str(sample_data)
    result = filter_endpoint(sample_data, "/non/existent", [Method.GET])
    assert str(result) == original_data_str


def test_data_without_paths_key():
    data = {"info": {"title": "Test"}}
    result = filter_endpoint(data, "/pet", [])
    assert "paths" not in result


def test_methods_to_keep_is_all_methods(sample_data):
    methods_to_keep = [Method.GET, Method.POST, Method.DELETE]
    original_data_str = str(sample_data["paths"]["/pet/{petId}"])
    result = filter_endpoint(sample_data, "/pet/{petId}", methods_to_keep)
    assert str(result["paths"]["/pet/{petId}"]) == original_data_str
