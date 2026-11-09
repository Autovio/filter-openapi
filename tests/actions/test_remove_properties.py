import pytest

from filter_openapi import remove_properties


@pytest.fixture
def sample_data():
    return {
        "info": {"title": "Test API", "version": "1.0.0", "x-oaiMeta": "some-meta"},
        "paths": {
            "/test": {
                "get": {
                    "summary": "Test endpoint",
                    "x-oaiMeta": "get-meta",
                    "responses": {
                        "200": {
                            "description": "OK",
                            "x-oaiMeta": "response-meta",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "x-oaiMeta": "schema-meta",
                                    }
                                }
                            },
                        }
                    },
                }
            }
        },
        "components": {
            "schemas": {
                "TestSchema": {
                    "type": "object",
                    "properties": {"id": {"type": "string"}},
                    "x-oaiMeta": "component-meta",
                }
            }
        },
        "tags": [
            {"name": "tag1", "x-oaiMeta": "tag-meta"},
            {"name": "tag2"},
        ],
    }


def test_remove_properties(sample_data):
    properties_to_remove = ["x-oaiMeta"]
    result = remove_properties(sample_data, properties_to_remove)

    assert "x-oaiMeta" not in result["info"]
    assert "x-oaiMeta" not in result["paths"]["/test"]["get"]
    assert "x-oaiMeta" not in result["paths"]["/test"]["get"]["responses"]["200"]
    assert (
        "x-oaiMeta"
        not in result["paths"]["/test"]["get"]["responses"]["200"]["content"][
            "application/json"
        ]["schema"]
    )
    assert "x-oaiMeta" not in result["components"]["schemas"]["TestSchema"]
    assert "x-oaiMeta" not in result["tags"][0]
    assert "name" in result["tags"][0]
    assert "name" in result["tags"][1]


def test_remove_multiple_properties(sample_data):
    sample_data["info"]["another-prop"] = "to-be-removed"
    properties_to_remove = ["x-oaiMeta", "another-prop"]
    result = remove_properties(sample_data, properties_to_remove)

    assert "x-oaiMeta" not in result["info"]
    assert "another-prop" not in result["info"]
    assert "title" in result["info"]


def test_no_properties_to_remove(sample_data):
    import json

    original_data_str = json.dumps(sample_data, sort_keys=True)
    result = remove_properties(sample_data, [])
    assert json.dumps(result, sort_keys=True) == original_data_str


def test_property_not_present(sample_data):
    import json

    original_data_str = json.dumps(sample_data, sort_keys=True)
    result = remove_properties(sample_data, ["non-existent-prop"])
    assert json.dumps(result, sort_keys=True) == original_data_str


def test_empty_data():
    assert remove_properties({}, ["x-oaiMeta"]) == {}
    assert remove_properties([], ["x-oaiMeta"]) == []
