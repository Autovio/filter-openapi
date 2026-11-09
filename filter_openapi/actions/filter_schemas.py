import logging
import re

logger = logging.getLogger(__name__)


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

    logger.info(
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

    logger.info(
        f"Removed {removed_count} unreferenced schemas, kept {len(filtered)} schemas"
    )
    if removed_count > 0:
        logger.debug(
            "Removed schemas: "
            + ", ".join(sorted(set(schemas.keys()) - referenced_schemas))
        )

    openapi_data["components"]["schemas"] = filtered
    return openapi_data
