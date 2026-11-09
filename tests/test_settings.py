import json

import pytest

from filter_openapi.settings import AppConfig, Options, PathFilter


def test_app_config_from_file(tmp_path):
    config_data = {
        "allowedTags": ["Pet", "Store"],
        "pathFilters": {
            "/pet/{petId}": {"allowedMethods": ["GET", "POST", "DELETE"]},
            "/pet/findByStatus": {"allowedMethods": ["GET"]},
        },
        "propertiesToRemove": ["x-oaiMeta"],
        "options": {"removeUnreferencedSchemas": True},
    }
    config_file = tmp_path / "config.json"
    with open(config_file, "w") as f:
        json.dump(config_data, f)

    app_config = AppConfig.from_file(str(config_file))
    assert app_config.allowed_tags == {"Pet", "Store"}
    assert "/pet/{petId}" in app_config.path_filters
    assert app_config.path_filters["/pet/{petId}"].allowed_methods == [
        "GET",
        "POST",
        "DELETE",
    ]
    assert app_config.properties_to_remove == ["x-oaiMeta"]
    assert app_config.options.remove_unreferenced_schemas is True


def test_app_config_defaults():
    config_data = {
        "allowedTags": ["Pet"],
        "pathFilters": {},
    }
    app_config = AppConfig.from_dict(config_data)
    assert app_config.properties_to_remove == []
    assert app_config.options.remove_unreferenced_schemas is True
    assert isinstance(app_config.options, Options)


def test_app_config_missing_required_fields():
    with pytest.raises(ValueError):
        AppConfig.from_dict({})  # Missing allowedTags and pathFilters

    with pytest.raises(ValueError):
        AppConfig.from_dict({"allowedTags": ["Pet"]})  # Missing pathFilters

    with pytest.raises(ValueError):
        AppConfig.from_dict({"pathFilters": {}})  # Missing allowedTags


def test_path_filter_missing_allowed_methods():
    with pytest.raises(ValueError):
        PathFilter.from_dict({})


def test_app_config_from_file_not_found():
    with pytest.raises(FileNotFoundError):
        AppConfig.from_file("non_existent_file.json")
