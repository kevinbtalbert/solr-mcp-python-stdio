"""Tests for Solr configuration."""

import json
from unittest.mock import mock_open, patch

import pytest

from solr_mcp.solr.config import SolrConfig
from solr_mcp.solr.exceptions import ConfigurationError


def test_config_defaults():
    """Test default configuration values."""
    config = SolrConfig(
        solr_base_url="http://test:8983/solr", zookeeper_hosts=["test:2181"]
    )
    assert config.solr_base_url == "http://test:8983/solr"
    assert config.zookeeper_hosts == ["test:2181"]
    assert config.connection_timeout == 10


def test_config_custom_values():
    """Test custom configuration values."""
    config = SolrConfig(
        solr_base_url="http://custom:8983/solr",
        zookeeper_hosts=["custom:2181"],
        connection_timeout=20,
    )
    assert config.solr_base_url == "http://custom:8983/solr"
    assert config.zookeeper_hosts == ["custom:2181"]
    assert config.connection_timeout == 20


def test_config_validation():
    """Test configuration validation."""
    with pytest.raises(ConfigurationError, match="solr_base_url is required"):
        SolrConfig(zookeeper_hosts=["test:2181"])

    with pytest.raises(ConfigurationError, match="connection_timeout must be positive"):
        SolrConfig(
            solr_base_url="http://test:8983/solr",
            zookeeper_hosts=["test:2181"],
            connection_timeout=0,
        )


def test_load_from_file():
    """Test loading configuration from file."""
    config_data = {
        "solr_base_url": "http://test:8983/solr",
        "zookeeper_hosts": ["test:2181"],
        "connection_timeout": 20,
    }

    with patch("builtins.open", mock_open(read_data=json.dumps(config_data))):
        config = SolrConfig.load("config.json")
        assert config.solr_base_url == "http://test:8983/solr"
        assert config.zookeeper_hosts == ["test:2181"]
        assert config.connection_timeout == 20


def test_load_invalid_json():
    """Test loading invalid JSON."""
    with patch("builtins.open", mock_open(read_data="invalid json")):
        with pytest.raises(
            ConfigurationError, match="Invalid JSON in configuration file"
        ):
            SolrConfig.load("config.json")


def test_load_url_only_config():
    """Test loading config with only Solr URL (no ZooKeeper)."""
    config_data = {"solr_base_url": "https://solr.example.com/solr"}

    with patch("builtins.open", mock_open(read_data=json.dumps(config_data))):
        config = SolrConfig.load("config.json")
        assert config.solr_base_url == "https://solr.example.com/solr"
        assert config.zookeeper_hosts == []


def test_config_url_only_defaults():
    """Solr URL alone is valid; collections use HTTP discovery."""
    config = SolrConfig(solr_base_url="https://solr.example.com/solr")
    assert config.zookeeper_hosts == []
