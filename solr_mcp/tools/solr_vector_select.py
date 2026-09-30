"""Tool for executing vector search queries against Solr collections."""

from typing import Dict, List, Optional

from solr_mcp.tools._context import get_solr_client
from solr_mcp.tools.tool_decorator import tool


@tool(name="vector-select")
async def execute_vector_select_query(
    query: str, vector: List[float], field: Optional[str] = None
) -> Dict:
    """Vector similarity search combined with SQL filtering (advanced).

    Extends sql-select with a query vector matched against a dense_vector/knn_vector
    field. ORDER BY is not allowed in ``query``.

    Parameters:
    - query: SQL query to execute
    - vector: Query vector (dimensions must match the vector field)
    - field: Vector field name (optional; auto-detected when omitted)
    """
    client = get_solr_client()
    return await client.execute_vector_select_query(query, vector, field)
