"""Tool for getting information about the default vector provider."""

from typing import Any, Dict
from urllib.parse import urlparse

from solr_mcp.tools._context import get_solr_client
from solr_mcp.tools.tool_decorator import tool
from solr_mcp.vector_provider.constants import DEFAULT_OLLAMA_CONFIG, MODEL_DIMENSIONS


@tool(name="get-default-text-vectorizer")
async def get_default_text_vectorizer() -> Dict[str, Any]:
    """Get the default embedding model used for semantic-select.

    Returns model name, vector dimensionality, and service URL. Use this to ensure
    Solr vector fields match the embedding model dimensions.
    """
    client = get_solr_client()
    vector_manager = client.vector_manager
    model_name = vector_manager.client.model
    dimension = MODEL_DIMENSIONS.get(model_name, 768)
    base_url = vector_manager.client.base_url

    if not model_name:
        model_name = DEFAULT_OLLAMA_CONFIG["model"]
        dimension = MODEL_DIMENSIONS.get(model_name, 768)
        base_url = DEFAULT_OLLAMA_CONFIG["base_url"]

    parsed_url = urlparse(base_url)
    host = parsed_url.hostname or "localhost"
    port = parsed_url.port or 11434
    formatted_spec = f"{model_name}@{host}:{port}"

    return {
        "vector_provider_model": model_name,
        "vector_provider_dimension": dimension,
        "vector_provider_host": host,
        "vector_provider_port": port,
        "vector_provider_url": base_url,
        "vector_provider_spec": formatted_spec,
    }
