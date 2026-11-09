import logging

logger = logging.getLogger(__name__)


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
