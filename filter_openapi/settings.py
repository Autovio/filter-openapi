import json
from dataclasses import dataclass, field
from typing import Any


def _require(data: dict[str, Any], key: str) -> Any:
    if key not in data:
        raise ValueError(f"Missing required config field: '{key}'")
    return data[key]


@dataclass
class Options:
    remove_unreferenced_schemas: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Options":
        return cls(
            remove_unreferenced_schemas=bool(
                data.get("removeUnreferencedSchemas", True)
            )
        )


@dataclass
class PathFilter:
    allowed_methods: list[str]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PathFilter":
        return cls(allowed_methods=list(_require(data, "allowedMethods")))


@dataclass
class AppConfig:
    allowed_tags: set[str]
    path_filters: dict[str, PathFilter]
    keep_operation_ids: set[str] = field(default_factory=set)
    properties_to_remove: list[str] = field(default_factory=list)
    options: Options = field(default_factory=Options)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AppConfig":
        return cls(
            allowed_tags=set(_require(data, "allowedTags")),
            path_filters={
                path: PathFilter.from_dict(path_filter)
                for path, path_filter in _require(data, "pathFilters").items()
            },
            keep_operation_ids=set(data.get("keepOperationIds", [])),
            properties_to_remove=list(data.get("propertiesToRemove", [])),
            options=Options.from_dict(data.get("options", {})),
        )

    @classmethod
    def from_file(cls, path: str) -> "AppConfig":
        """Loads configuration from a JSON file."""
        with open(path, "r") as f:
            data = json.load(f)
        return cls.from_dict(data)
