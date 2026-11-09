import argparse
import json
import logging
import re
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Optional

logger = logging.getLogger(__name__)


# Settings


@dataclass
class Options:
    removeUnreferencedSchemas: bool = True


@dataclass
class PathFilter:
    allowedMethods: list[str] = field(default_factory=list)


@dataclass
class AppConfig:
    allowedTags: set[str] | None = None
    pathFilters: dict[str, PathFilter] = field(default_factory=dict)
    keepOperationIds: set[str] = field(default_factory=set)
    propertiesToRemove: list[str] = field(default_factory=list)
    options: Options = field(default_factory=Options)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AppConfig":
        data = dict(data)
        if "allowedTags" in data:
            data["allowedTags"] = set(data["allowedTags"])
        data["keepOperationIds"] = set(data.get("keepOperationIds", []))
        data["pathFilters"] = {
            path: PathFilter(**path_filter)
            for path, path_filter in data.get("pathFilters", {}).items()
        }
        data["options"] = Options(**data.get("options", {}))
        return cls(**data)

    @classmethod
    def from_file(cls, path: str) -> "AppConfig":
        with open(path, "r") as f:
            return cls.from_dict(json.load(f))


# Actions


class Method(str, Enum):
    """HTTP methods that can be filtered in an endpoint."""

    GET = "get"
    POST = "post"
    PUT = "put"
    DELETE = "delete"
    PATCH = "patch"
    HEAD = "head"
    OPTIONS = "options"


def filter_endpoint(
    openapi_data, path: str, methods_to_keep: Optional[List[Method]] = None
) -> dict:
    """Filter methods for a path in the OpenAPI spec, keeping only specified methods.

    Args:
        openapi_data: The OpenAPI specification dictionary
        path: The path to filter (e.g., "/chat/completions")
        methods_to_keep: List of Method enum values to keep. If None or empty list,
                        the entire path is removed.

    Returns:
        Modified OpenAPI data
    """
    if not isinstance(openapi_data, dict) or "paths" not in openapi_data:
        logger.warning("Input data has no paths to process")
        return openapi_data

    paths = openapi_data["paths"]
    if path not in paths:
        logger.debug(f"Path {path} not found")
        return openapi_data

    # If no methods specified, remove the entire path
    if not methods_to_keep:
        logger.debug(f"Removing entire path: {path}")
        methods = list(paths[path].keys())
        if methods:
            logger.debug(f"Removing methods: {', '.join(methods).upper()}")
        del paths[path]
        return openapi_data

    # Convert methods to keep to lowercase strings for comparison
    allowed_methods = {m.value for m in methods_to_keep}

    # Get current methods for logging
    current_methods = set(paths[path].keys())
    methods_to_remove = current_methods - allowed_methods

    if methods_to_remove:
        logger.debug(f"Filtering methods for {path}")
        logger.debug(f"Keeping methods: {', '.join(allowed_methods).upper()}")
        logger.debug(f"Removing methods: {', '.join(methods_to_remove).upper()}")

        # Remove methods not in the allowed list
        for method in methods_to_remove:
            del paths[path][method]

        # If no methods left after filtering, remove the entire path
        if not paths[path]:
            logger.debug(f"Removing {path} path (no methods remaining after filter)")
            del paths[path]
    else:
        logger.debug(f"No methods to filter for {path}")

    return openapi_data


def filter_paths_by_tags(openapi_data, allowed_tags, keep_operation_ids=frozenset()):
    """Keep operations that have an allowed tag or a listed operationId."""
    if not isinstance(openapi_data, dict) or "paths" not in openapi_data:
        logger.warning("Input data has no paths to filter")
        return openapi_data

    paths = openapi_data["paths"]
    original_path_count = len(paths)
    filtered_paths = {}

    for path, methods in paths.items():
        logger.debug(f"Processing path: {path}")
        filtered_methods = {}
        for method, op in methods.items():
            tags = op.get("tags", [])
            operation_id = op.get("operationId")
            if any(tag in allowed_tags for tag in tags):
                filtered_methods[method] = op
                logger.debug(
                    f"Keeping {method.upper()} {path} (tags: {', '.join(tags)})"
                )
            elif operation_id in keep_operation_ids:
                filtered_methods[method] = op
                logger.debug(
                    f"Keeping {method.upper()} {path} (operationId: {operation_id})"
                )
            else:
                logger.debug(
                    f"Removing {method.upper()} {path} (tags: {', '.join(tags)})"
                )
        if filtered_methods:
            filtered_paths[path] = filtered_methods

    removed_paths = original_path_count - len(filtered_paths)
    logger.debug(f"Removed {removed_paths} paths, kept {len(filtered_paths)} paths")
    openapi_data["paths"] = filtered_paths
    return openapi_data


def find_all_refs(obj):
    """Recursively find all $ref values in a JSON object."""
    refs = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "$ref" and isinstance(v, str):
                refs.add(v)
                logger.debug(f"Found reference: {v}")
            else:
                refs.update(find_all_refs(v))
    elif isinstance(obj, list):
        for item in obj:
            refs.update(find_all_refs(item))
    return refs


def get_referenced_schemas(openapi_data):
    """Return the set of all schema names that are directly or indirectly referenced from paths."""
    if not isinstance(openapi_data, dict):
        logger.warning("Input data is not a dictionary")
        return set()
    schemas = openapi_data.get("components", {}).get("schemas", {})
    if not schemas:
        logger.warning("No schemas found in components")
        return set()

    # 1. Find all $ref in paths
    logger.debug("Finding references in paths")
    root_refs = find_all_refs(openapi_data.get("paths", {}))
    logger.debug(f"Found {len(root_refs)} references in paths")

    # Only consider refs to #/components/schemas/SchemaName
    schema_ref_pattern = re.compile(r"^#/components/schemas/([^/]+)$")
    referenced = set()
    queue = []
    for ref in root_refs:
        m = schema_ref_pattern.match(ref)
        if m:
            schema_name = m.group(1)
            referenced.add(schema_name)
            queue.append(schema_name)
            logger.debug(f"Found root schema reference: {schema_name}")

    # 2. Recursively find all $ref in referenced schemas
    logger.debug("Finding nested schema references")
    while queue:
        schema_name = queue.pop()
        schema = schemas.get(schema_name)
        if not schema:
            logger.warning(f"Referenced schema not found: {schema_name}")
            continue
        for ref in find_all_refs(schema):
            m = schema_ref_pattern.match(ref)
            if m:
                sub_schema = m.group(1)
                if sub_schema not in referenced:
                    referenced.add(sub_schema)
                    queue.append(sub_schema)
                    logger.debug(f"Found nested schema reference: {sub_schema}")

    logger.debug(
        f"Found {len(referenced)} referenced schemas out of {len(schemas)} total schemas"
    )
    return referenced


def filter_schemas(openapi_data, referenced_schemas):
    if not isinstance(openapi_data, dict):
        logger.warning("Input data is not a dictionary")
        return openapi_data
    if "components" not in openapi_data or "schemas" not in openapi_data["components"]:
        logger.warning("No schemas section found in components")
        return openapi_data

    schemas = openapi_data["components"]["schemas"]
    original_count = len(schemas)
    filtered = {k: v for k, v in schemas.items() if k in referenced_schemas}
    removed_count = original_count - len(filtered)

    logger.debug(
        f"Removed {removed_count} unreferenced schemas, kept {len(filtered)} schemas"
    )
    if removed_count > 0:
        logger.debug(
            "Removed schemas: "
            + ", ".join(sorted(set(schemas.keys()) - referenced_schemas))
        )

    openapi_data["components"]["schemas"] = filtered
    return openapi_data


def filter_tags_list(openapi_data, allowed_tags):
    """Remove tags from the top-level tags list that are not in allowed_tags."""
    if not isinstance(openapi_data, dict):
        logger.warning("Input data is not a dictionary")
        return openapi_data

    if "tags" not in openapi_data:
        logger.debug("No top-level tags list found in OpenAPI spec")
        return openapi_data

    original_tags = openapi_data["tags"]
    if not isinstance(original_tags, list):
        logger.warning("Top-level tags is not a list")
        return openapi_data

    # Filter tags list to keep only allowed tags
    filtered_tags = [
        tag
        for tag in original_tags
        if isinstance(tag, dict) and tag.get("name") in allowed_tags
    ]

    removed_count = len(original_tags) - len(filtered_tags)
    logger.debug(f"Removed {removed_count} tags, kept {len(filtered_tags)} tags")
    if removed_count > 0:
        removed_names = [
            tag.get("name")
            for tag in original_tags
            if isinstance(tag, dict) and tag.get("name") not in allowed_tags
        ]
        logger.debug(f"Removed tags: {', '.join(removed_names)}")

    openapi_data["tags"] = filtered_tags
    return openapi_data


def remove_properties(obj: Any, properties_to_remove: List[str]) -> Any:
    """
    Recursively remove specified properties from a nested object (dict or list).

    :param obj: The object to process (dict or list).
    :param properties_to_remove: A list of property names (keys) to remove.
    :return: The modified object.
    """
    if isinstance(obj, dict):
        # Keys to remove from the current dictionary
        keys_in_obj = set(obj.keys())
        properties_set = set(properties_to_remove)
        keys_to_remove_from_current_obj = keys_in_obj & properties_set

        if keys_to_remove_from_current_obj:
            logger.debug(
                f"Removing properties: {', '.join(sorted(keys_to_remove_from_current_obj))}"
            )
            obj = {k: v for k, v in obj.items() if k not in properties_to_remove}

        # Recursively process values
        return {k: remove_properties(v, properties_to_remove) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [remove_properties(item, properties_to_remove) for item in obj]
    else:
        return obj


# CLI


def setup_logging(verbose=False):
    """Configure logging with appropriate level and format."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main():
    parser = argparse.ArgumentParser(
        description="Modify an OpenAPI specification JSON doc for OpenAI's API."
    )
    parser.add_argument("input_file", help="Path to the input OpenAPI JSON file.")
    parser.add_argument(
        "-c",
        "--config",
        dest="config_file",
        required=True,
        help="Path to the configuration JSON file.",
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="output_file",
        help="Path to the output file. If not provided, output is written to stdout.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose (DEBUG) logging",
    )
    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)
    logger.debug("Starting OpenAPI specification modification")
    logger.debug(f"Input file: {args.input_file}")
    logger.debug(f"Config file: {args.config_file}")
    logger.debug(
        f"Output destination: {'stdout' if not args.output_file else args.output_file}"
    )

    # Read config file
    try:
        logger.debug(f"Loading configuration from {args.config_file}")
        config = AppConfig.from_file(args.config_file)
        logger.debug("Successfully loaded configuration")
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        sys.exit(1)

    # Read the input JSON file
    try:
        logger.debug("Reading input JSON file")
        with open(args.input_file, "r") as f:
            json_content = f.read()
        logger.debug(f"Successfully read {len(json_content)} bytes from input file")
    except Exception as e:
        logger.error(f"Error reading input file: {e}")
        sys.exit(1)

    # Parse JSON
    try:
        logger.debug("Parsing JSON content")
        data = json.loads(json_content)
        logger.debug("Successfully parsed JSON content")
    except Exception as e:
        logger.error(f"Error parsing JSON: {e}")
        sys.exit(1)

    # Remove all 'x-oaiMeta' properties
    if config.propertiesToRemove:
        logger.debug(
            f"Removing properties: {', '.join(sorted(config.propertiesToRemove))}"
        )
        data = remove_properties(data, config.propertiesToRemove)

    allowed_tags = config.allowedTags
    keep_operation_ids = config.keepOperationIds

    if allowed_tags is None and not keep_operation_ids:
        logger.debug(
            "No allowedTags or keepOperationIds configured, keeping all paths and tags"
        )
    else:
        allowed_tags = allowed_tags or set()

        # Filter paths by allowed tags and operationIds
        logger.debug(f"Filtering paths by tags: {', '.join(sorted(allowed_tags))}")
        if keep_operation_ids:
            logger.debug(
                f"Also keeping operationIds: {', '.join(sorted(keep_operation_ids))}"
            )
        data = filter_paths_by_tags(data, allowed_tags, keep_operation_ids)

        # Keep top-level tags used by operations kept via operationId
        tags_to_keep = set(allowed_tags)
        for methods in data.get("paths", {}).values():
            for op in methods.values():
                if op.get("operationId") in keep_operation_ids:
                    tags_to_keep.update(op.get("tags", []))

        # Filter top-level tags list
        logger.debug("Filtering top-level tags list")
        data = filter_tags_list(data, tags_to_keep)

    # Filter specific endpoints based on config
    logger.debug("Filtering specific endpoints based on configuration")
    for path, path_filter in config.pathFilters.items():
        methods_to_keep = [Method(m.lower()) for m in path_filter.allowedMethods]
        if methods_to_keep:
            logger.debug(
                f"Filtering path '{path}', keeping methods: {[m.upper() for m in path_filter.allowedMethods]}"
            )
        else:
            logger.debug(f"Removing path '{path}'")
        data = filter_endpoint(
            data,
            path,
            methods_to_keep,
        )

    # Remove unreferenced schemas
    if config.options.removeUnreferencedSchemas:
        logger.debug("Removing unreferenced schemas")
        referenced_schemas = get_referenced_schemas(data)
        logger.debug(f"Found {len(referenced_schemas)} referenced schemas")
        data = filter_schemas(data, referenced_schemas)

    # Dump JSON
    try:
        logger.debug("Converting modified data back to JSON")
        output_json = json.dumps(data, indent=2, ensure_ascii=False)
        logger.debug(f"Generated {len(output_json)} bytes of JSON output")
    except Exception as e:
        logger.error(f"Error dumping JSON: {e}")
        sys.exit(1)

    # Write to output file or stdout
    if args.output_file:
        try:
            logger.debug(f"Writing output to file: {args.output_file}")
            with open(args.output_file, "w") as f:
                f.write(output_json)
            logger.debug("Successfully wrote output file")
        except Exception as e:
            logger.error(f"Error writing to output file: {e}")
            sys.exit(1)
    else:
        logger.debug("Writing output to stdout")
        print(output_json)

    logger.debug("OpenAPI specification modification completed")


if __name__ == "__main__":
    main()
