"""Shared Solr client for MCP tools (no injected ``mcp`` parameter)."""

import os
from typing import List, Optional

from solr_mcp.solr.client import SolrClient
from solr_mcp.solr.config import SolrConfig

_client: Optional[SolrClient] = None


def _parse_zookeeper_hosts(raw: str | None) -> List[str]:
    if raw is None or not raw.strip():
        return []
    return [host.strip() for host in raw.split(",") if host.strip()]


def get_solr_client() -> SolrClient:
    """Return a process-wide SolrClient configured from environment variables."""
    global _client
    if _client is None:
        config = SolrConfig(
            solr_base_url=os.getenv("SOLR_BASE_URL", "http://localhost:8983/solr"),
            zookeeper_hosts=_parse_zookeeper_hosts(os.getenv("ZOOKEEPER_HOSTS")),
            connection_timeout=int(os.getenv("CONNECTION_TIMEOUT", "10")),
        )
        _client = SolrClient(config=config)
    return _client


def set_solr_client(client: Optional[SolrClient]) -> None:
    """Replace the shared client (used in unit tests)."""
    global _client
    _client = client
