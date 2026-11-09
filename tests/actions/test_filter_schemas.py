import pytest

from filter_openapi import (
    filter_schemas,
    get_referenced_schemas,
)


@pytest.fixture
def sample_data():
    return {
        "paths": {
            "/items": {
                "get": {
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ItemList"}
                                }
                            }
                        }
                    }
                }
            },
            "/items/{itemId}": {
                "get": {
                    "parameters": [
                        {
                            "name": "itemId",
                            "in": "path",
                            "schema": {"$ref": "#/components/schemas/ItemId"},
                        }
                    ],
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Item"}
                                }
                            }
                        }
                    },
                },
                "post": {
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Item"}
                            }
                        }
                    }
                },
            },
        },
        "components": {
            "schemas": {
                "ItemId": {"type": "string", "format": "uuid"},
                "ItemList": {
                    "type": "array",
                    "items": {"$ref": "#/components/schemas/Item"},
                },
                "Item": {
                    "type": "object",
                    "properties": {
                        "id": {"$ref": "#/components/schemas/ItemId"},
                        "name": {"type": "string"},
                        "tag": {"$ref": "#/components/schemas/Tag"},
                        "history": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/HistoryEvent"},
                        },
                    },
                },
                "Tag": {"type": "string"},
                "HistoryEvent": {
                    "type": "object",
                    "properties": {
                        "timestamp": {"type": "string", "format": "date-time"},
                        "user": {"$ref": "#/components/schemas/User"},
                    },
                },
                "User": {"type": "object", "properties": {"name": {"type": "string"}}},
                "UnreferencedSchema": {
                    "type": "object",
                    "properties": {"foo": {"type": "string"}},
                },
                "AlsoUnreferenced": {"type": "string"},
            }
        },
    }


def test_get_referenced_schemas(sample_data):
    refs = get_referenced_schemas(sample_data)
    expected_refs = {"ItemId", "ItemList", "Item", "Tag", "HistoryEvent", "User"}
    assert refs == expected_refs


def test_get_referenced_schemas_no_refs():
    data = {"paths": {"/foo": {"get": {"description": "bar"}}}}
    refs = get_referenced_schemas(data)
    assert refs == set()


def test_filter_schemas(sample_data):
    referenced_schemas = get_referenced_schemas(sample_data)
    result = filter_schemas(sample_data, referenced_schemas)

    final_schemas = result["components"]["schemas"]
    assert "ItemList" in final_schemas
    assert "Item" in final_schemas
    assert "ItemId" in final_schemas
    assert "Tag" in final_schemas
    assert "HistoryEvent" in final_schemas
    assert "User" in final_schemas
    assert "UnreferencedSchema" not in final_schemas
    assert "AlsoUnreferenced" not in final_schemas


def test_filter_schemas_no_components():
    data = {"paths": {}}
    result = filter_schemas(data, set())
    assert "components" not in result


def test_filter_schemas_no_schemas_in_components():
    data = {"components": {"parameters": {}}}
    result = filter_schemas(data, set())
    assert "schemas" not in result["components"]


def test_circular_reference():
    data = {
        "paths": {
            "/a": {
                "get": {
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/SchemaA"}
                                }
                            }
                        }
                    }
                }
            }
        },
        "components": {
            "schemas": {
                "SchemaA": {
                    "properties": {"b": {"$ref": "#/components/schemas/SchemaB"}}
                },
                "SchemaB": {
                    "properties": {"a": {"$ref": "#/components/schemas/SchemaA"}}
                },
                "SchemaC": {"type": "string"},
            }
        },
    }
    refs = get_referenced_schemas(data)
    assert refs == {"SchemaA", "SchemaB"}
    result = filter_schemas(data, refs)
    assert "SchemaA" in result["components"]["schemas"]
    assert "SchemaB" in result["components"]["schemas"]
    assert "SchemaC" not in result["components"]["schemas"]
