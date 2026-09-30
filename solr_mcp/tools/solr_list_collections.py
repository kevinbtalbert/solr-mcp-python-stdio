"""Tool for listing Solr collections."""

from typing import List

from solr_mcp.tools._context import get_solr_client
from solr_mcp.tools.tool_decorator import tool


@tool(name="list-collections")
async def list_collections() -> List[str]:
    """List all available Solr collections in the cluster."""
    client = get_solr_client()
    return await client.list_collections()
