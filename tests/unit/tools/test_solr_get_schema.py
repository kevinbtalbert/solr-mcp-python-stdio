"""Tests for get-schema tool."""

from unittest.mock import MagicMock

import pytest

from solr_mcp.tools import _context
from solr_mcp.tools.solr_get_schema import get_collection_schema
from solr_mcp.solr.exceptions import SchemaError, SolrError


@pytest.fixture(autouse=True)
def reset_solr_client():
    _context.set_solr_client(None)
    yield
    _context.set_solr_client(None)


@pytest.mark.asyncio
async def test_get_collection_schema_success():
    mock_solr_client = MagicMock()
    mock_solr_client.field_manager.get_schema.return_value = {
        "fields": [{"name": "id", "type": "string"}]
    }
    _context.set_solr_client(mock_solr_client)

    result = await get_collection_schema("test_collection")

    assert result == {
        "collection": "test_collection",
        "schema": {"fields": [{"name": "id", "type": "string"}]},
    }


@pytest.mark.asyncio
async def test_get_collection_schema_not_found():
    mock_solr_client = MagicMock()
    mock_solr_client.field_manager.get_schema.side_effect = SchemaError(
        "Collection not found: missing"
    )
    _context.set_solr_client(mock_solr_client)

    with pytest.raises(SchemaError, match="list-collections"):
        await get_collection_schema("missing")
