"""Tests for Solr MCP tools."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from solr_mcp.tools import _context
from solr_mcp.tools.solr_get_schema import get_collection_schema
from solr_mcp.tools.solr_list_collections import list_collections
from solr_mcp.tools.solr_search import search
from solr_mcp.tools.solr_select import execute_select_query
from solr_mcp.tools.solr_semantic_select import execute_semantic_select_query
from solr_mcp.tools.solr_vector_select import execute_vector_select_query


@pytest.fixture(autouse=True)
def reset_solr_client():
    _context.set_solr_client(None)
    yield
    _context.set_solr_client(None)


@pytest.mark.asyncio
class TestListCollectionsTool:
    """Test list collections tool."""

    async def test_list_collections(self):
        mock_solr_client = AsyncMock()
        mock_solr_client.list_collections.return_value = ["collection1", "collection2"]
        _context.set_solr_client(mock_solr_client)

        result = await list_collections()

        assert result == ["collection1", "collection2"]
        mock_solr_client.list_collections.assert_called_once()


@pytest.mark.asyncio
class TestGetSchemaTool:
    """Test get-schema tool."""

    async def test_get_collection_schema(self):
        mock_solr_client = MagicMock()
        mock_solr_client.field_manager.get_schema.return_value = {
            "fields": [{"name": "id", "type": "string"}]
        }
        _context.set_solr_client(mock_solr_client)

        result = await get_collection_schema("test")

        assert result["collection"] == "test"
        assert "fields" in result["schema"]
        mock_solr_client.field_manager.get_schema.assert_called_once_with("test")


@pytest.mark.asyncio
class TestSearchTool:
    """Test search tool."""

    async def test_search_formats_results(self):
        mock_solr_client = MagicMock()
        mock_solr_client.base_url = "http://localhost:8983/solr"
        mock_solr_client.config.connection_timeout = 10
        mock_solr_client.response_formatter.format_search_results.return_value = (
            '{"result-set": {"numFound": 1, "start": 0, "docs": [{"id": "1"}]}}'
        )
        _context.set_solr_client(mock_solr_client)

        mock_results = MagicMock()

        async def run_sync(fn):
            return fn()

        with patch(
            "solr_mcp.tools.solr_search.asyncio.to_thread", side_effect=run_sync
        ):
            with patch("solr_mcp.tools.solr_search.pysolr.Solr") as mock_solr_cls:
                mock_solr_cls.return_value.search.return_value = mock_results
                result = await search("films", query="title:war")

        assert result["result-set"]["numFound"] == 1
        mock_solr_client.response_formatter.format_search_results.assert_called_once()


@pytest.mark.asyncio
class TestSelectQueryTool:
    """Test select query tool."""

    async def test_execute_select_query(self):
        mock_solr_client = AsyncMock()
        mock_solr_client.execute_select_query.return_value = {"rows": [{"id": "1"}]}
        _context.set_solr_client(mock_solr_client)

        query = "SELECT * FROM collection1"
        result = await execute_select_query(query)

        assert result == {"rows": [{"id": "1"}]}
        mock_solr_client.execute_select_query.assert_called_once_with(query)


@pytest.mark.asyncio
class TestVectorSelectTool:
    """Test vector select query tool."""

    async def test_execute_vector_select_query(self):
        mock_solr_client = AsyncMock()
        mock_solr_client.execute_vector_select_query.return_value = {
            "rows": [{"id": "1"}]
        }
        _context.set_solr_client(mock_solr_client)

        query = "SELECT * FROM collection1"
        vector = [0.1, 0.2, 0.3]
        field = "vector_field"
        result = await execute_vector_select_query(query, vector, field)

        assert result == {"rows": [{"id": "1"}]}
        mock_solr_client.execute_vector_select_query.assert_called_once_with(
            query, vector, field
        )


@pytest.mark.asyncio
class TestSemanticSelectTool:
    """Test semantic select query tool."""

    async def test_execute_semantic_select_query(self):
        mock_solr_client = AsyncMock()
        mock_solr_client.execute_semantic_select_query.return_value = {
            "rows": [{"id": "1"}]
        }
        _context.set_solr_client(mock_solr_client)

        query = "SELECT * FROM collection1"
        text = "sample search text"
        field = "vector_field"
        result = await execute_semantic_select_query(query, text, field)

        assert result == {"rows": [{"id": "1"}]}
        mock_solr_client.execute_semantic_select_query.assert_called_once_with(
            query, text, field, {}
        )

    async def test_execute_semantic_select_query_with_vector_provider(self):
        mock_solr_client = AsyncMock()
        mock_solr_client.execute_semantic_select_query.return_value = {
            "rows": [{"id": "1"}]
        }
        _context.set_solr_client(mock_solr_client)

        query = "SELECT * FROM collection1"
        text = "sample search text"
        field = "vector_field"
        vector_provider = "custom-model@test-host:9999"

        result = await execute_semantic_select_query(
            query, text, field, vector_provider
        )

        assert result == {"rows": [{"id": "1"}]}
        expected_config = {"model": "custom-model", "base_url": "http://test-host:9999"}
        mock_solr_client.execute_semantic_select_query.assert_called_once_with(
            query, text, field, expected_config
        )


class TestToolMetadata:
    """Test tool metadata."""

    def test_official_tool_names(self):
        assert list_collections._tool_name == "list-collections"
        assert search._tool_name == "search"
        assert get_collection_schema._tool_name == "get-schema"
        assert execute_select_query._tool_name == "sql-select"
        assert execute_vector_select_query._tool_name == "vector-select"
        assert execute_semantic_select_query._tool_name == "semantic-select"
