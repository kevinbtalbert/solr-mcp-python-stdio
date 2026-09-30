"""Schema retrieval tool (aligned with upstream Solr MCP ``get-schema``)."""

from typing import Any, Dict

from solr_mcp.solr.exceptions import SchemaError, SolrError
from solr_mcp.tools._context import get_solr_client
from solr_mcp.tools.tool_decorator import tool


@tool(name="get-schema")
async def get_collection_schema(collection: str) -> Dict[str, Any]:
    """Retrieve schema information for a Solr collection.

    Returns field definitions, field types, and copy-field relationships from the
    Schema API. Call this before search when you need valid field names or types.

    Parameters:
    - collection: Solr collection name
    """
    client = get_solr_client()
    try:
        schema = client.field_manager.get_schema(collection)
        return {"collection": collection, "schema": schema}
    except SchemaError as exc:
        hint = str(exc)
        if "not found" in hint.lower():
            hint = (
                f"{hint} Use list-collections to see available collection names."
            )
        raise SchemaError(hint) from exc
    except Exception as exc:
        raise SolrError(f"Failed to get schema: {exc}") from exc
