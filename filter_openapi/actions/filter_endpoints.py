import logging
from enum import Enum
from typing import List, Optional

logger = logging.getLogger(__name__)


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
