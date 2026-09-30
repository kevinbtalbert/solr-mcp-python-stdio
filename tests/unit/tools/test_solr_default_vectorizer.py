"""Tests for get-default-text-vectorizer tool."""

from unittest.mock import MagicMock

import pytest

from solr_mcp.tools import _context
from solr_mcp.tools.solr_default_vectorizer import get_default_text_vectorizer
from solr_mcp.vector_provider.constants import DEFAULT_OLLAMA_CONFIG, MODEL_DIMENSIONS


@pytest.fixture(autouse=True)
def reset_solr_client():
    _context.set_solr_client(None)
    yield
    _context.set_solr_client(None)


class TestDefaultVectorizerTool:
    """Test cases for default_text_vectorizer tool."""

    @pytest.mark.asyncio
    async def test_get_default_text_vectorizer(self):
        mock_vector_manager = MagicMock()
        mock_vector_manager.client.model = "nomic-embed-text"
        mock_vector_manager.client.base_url = "http://test-host:8888"

        mock_solr_client = MagicMock()
        mock_solr_client.vector_manager = mock_vector_manager
        _context.set_solr_client(mock_solr_client)

        result = await get_default_text_vectorizer()

        assert result["vector_provider_model"] == "nomic-embed-text"
        assert result["vector_provider_dimension"] == 768
        assert result["vector_provider_host"] == "test-host"
        assert result["vector_provider_port"] == 8888
        assert result["vector_provider_url"] == "http://test-host:8888"
        assert result["vector_provider_spec"] == "nomic-embed-text@test-host:8888"

    @pytest.mark.asyncio
    async def test_get_default_text_vectorizer_unknown_model(self):
        mock_vector_manager = MagicMock()
        mock_vector_manager.client.model = "unknown-model"
        mock_vector_manager.client.base_url = "http://test-host:8888"

        mock_solr_client = MagicMock()
        mock_solr_client.vector_manager = mock_vector_manager
        _context.set_solr_client(mock_solr_client)

        result = await get_default_text_vectorizer()

        assert result["vector_provider_model"] == "unknown-model"
        assert result["vector_provider_dimension"] == 768
        assert result["vector_provider_spec"] == "unknown-model@test-host:8888"

    @pytest.mark.asyncio
    async def test_get_default_text_vectorizer_empty_model_uses_constants(self):
        mock_vector_manager = MagicMock()
        mock_vector_manager.client.model = ""
        mock_vector_manager.client.base_url = DEFAULT_OLLAMA_CONFIG["base_url"]

        mock_solr_client = MagicMock()
        mock_solr_client.vector_manager = mock_vector_manager
        _context.set_solr_client(mock_solr_client)

        result = await get_default_text_vectorizer()

        assert result["vector_provider_model"] == DEFAULT_OLLAMA_CONFIG["model"]
        assert (
            result["vector_provider_dimension"]
            == MODEL_DIMENSIONS[DEFAULT_OLLAMA_CONFIG["model"]]
        )
