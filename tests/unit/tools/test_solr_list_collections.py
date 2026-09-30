"""Tests for list-collections tool."""

from unittest.mock import AsyncMock

import pytest

from solr_mcp.solr.exceptions import SolrError
from solr_mcp.tools import _context
from solr_mcp.tools.solr_list_collections import list_collections


@pytest.fixture(autouse=True)
def reset_solr_client():
    _context.set_solr_client(None)
    yield
    _context.set_solr_client(None)


@pytest.mark.asyncio
class TestListCollectionsTool:
    """Test list collections tool."""

    async def test_list_collections_success(self):
        mock_solr_client = AsyncMock()
        mock_solr_client.list_collections.return_value = ["collection1", "collection2"]
        _context.set_solr_client(mock_solr_client)

        result = await list_collections()

        assert result == ["collection1", "collection2"]
        mock_solr_client.list_collections.assert_called_once()

    async def test_list_collections_error(self):
        mock_solr_client = AsyncMock()
        mock_solr_client.list_collections.side_effect = SolrError("Connection failed")
        _context.set_solr_client(mock_solr_client)

        with pytest.raises(SolrError, match="Connection failed"):
            await list_collections()
