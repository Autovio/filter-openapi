import logging

logger = logging.getLogger(__name__)


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
