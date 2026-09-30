"""Tool for executing semantic search queries against Solr collections."""

from typing import Dict, Optional

from solr_mcp.tools._context import get_solr_client
from solr_mcp.tools.tool_decorator import tool


@tool(name="semantic-select")
async def execute_semantic_select_query(
    query: str,
    text: str,
    field: Optional[str] = None,
    vector_provider: str = "",
) -> Dict:
    """Semantic (vector) search combined with SQL filtering (advanced).

    Extends sql-select with semantic search: natural language ``text`` is embedded
    and matched against a dense_vector/knn_vector field. Results rank by similarity;
    ORDER BY is not allowed in ``query``.

    Parameters:
    - query: SQL query to execute
    - text: Natural language text converted to a vector for similarity search
    - field: Vector field name (optional; auto-detected when omitted)
    - vector_provider: Optional ``model@host:port`` (e.g. nomic-embed-text@localhost:11434)
    """
    client = get_solr_client()
    vector_provider_config: Dict = {}

    if vector_provider:
        model_part = vector_provider
        host_port_part = None

        if "@" in vector_provider:
            parts = vector_provider.split("@", 1)
            model_part = parts[0]
            host_port_part = parts[1]

        if model_part:
            vector_provider_config["model"] = model_part

        if host_port_part:
            if ":" in host_port_part:
                host, port_str = host_port_part.split(":", 1)
                try:
                    port = int(port_str)
                    vector_provider_config["base_url"] = f"http://{host}:{port}"
                except ValueError:
                    vector_provider_config["base_url"] = f"http://{host_port_part}"
            else:
                vector_provider_config["base_url"] = f"http://{host_port_part}:11434"

    return await client.execute_semantic_select_query(
        query, text, field, vector_provider_config
    )
