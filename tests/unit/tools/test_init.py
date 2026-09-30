"""Test tools initialization."""

from solr_mcp.tools import (
    TOOLS_DEFINITION,
    execute_select_query,
    execute_semantic_select_query,
    execute_vector_select_query,
    get_collection_schema,
    get_default_text_vectorizer,
    list_collections,
    search,
)


def test_tools_definition():
    """Test that TOOLS_DEFINITION contains all expected tools."""
    tools = {
        "list-collections": list_collections,
        "search": search,
        "get-schema": get_collection_schema,
        "sql-select": execute_select_query,
        "vector-select": execute_vector_select_query,
        "semantic-select": execute_semantic_select_query,
        "get-default-text-vectorizer": get_default_text_vectorizer,
    }

    assert len(TOOLS_DEFINITION) == len(tools)

    for tool_func in tools.values():
        assert tool_func in TOOLS_DEFINITION


def test_tools_exports():
    """Test that __all__ exports all tools."""
    from solr_mcp.tools import __all__

    expected = {
        "list_collections",
        "search",
        "get_collection_schema",
        "execute_select_query",
        "execute_vector_select_query",
        "execute_semantic_select_query",
        "get_default_text_vectorizer",
    }

    assert set(__all__) == expected
