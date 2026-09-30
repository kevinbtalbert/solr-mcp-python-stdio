"""Lucene /select search tool (aligned with upstream Solr MCP ``search``)."""

import asyncio
import json
from typing import Any, Dict, List, Optional

import pysolr

from solr_mcp.solr.exceptions import QueryError
from solr_mcp.tools._context import get_solr_client
from solr_mcp.tools.tool_decorator import tool


def _remediation_hint(message: str) -> str:
    lower = message.lower()
    if "unknown field" in lower or "undefined field" in lower:
        return (
            f"{message} Use the get-schema tool on this collection to list valid "
            "field names."
        )
    if "collection not found" in lower or "404" in lower:
        return f"{message} Use list-collections to see available collection names."
    return message


@tool(name="search")
async def search(
    collection: str,
    query: Optional[str] = None,
    filter_queries: Optional[List[str]] = None,
    facet_fields: Optional[List[str]] = None,
    sort: Optional[str] = None,
    start: int = 0,
    rows: int = 10,
    fields: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Full-text search with filtering, faceting, sorting, and pagination.

    Queries Solr's ``/select`` handler using Lucene syntax. This is the preferred
    tool for natural-language questions about document content.

    Parameters:
    - collection: Solr collection name
    - query: Main query ``q`` (Lucene syntax). Defaults to ``*:*`` when omitted.
    - filter_queries: Optional filter queries (``fq``), applied without affecting score
    - facet_fields: Field names to facet on (enables ``facet=true``)
    - sort: Solr sort clause, e.g. ``score desc`` or ``year_i desc``
    - start: Pagination offset (default 0)
    - rows: Number of documents to return (default 10)
    - fields: Restrict returned stored fields (``fl``). Omit to return the default set.

    Examples:
    - ``collection=films``, ``query=title:star AND genre_s:sci-fi``
    - ``collection=films``, ``query=*:*``, ``filter_queries=['year_i:[2000 TO *]']``
    """
    client = get_solr_client()
    q = query if query else "*:*"
    search_kwargs: Dict[str, Any] = {"start": start, "rows": rows}
    if filter_queries:
        search_kwargs["fq"] = filter_queries
    if sort:
        search_kwargs["sort"] = sort
    if fields:
        search_kwargs["fl"] = ",".join(fields)
    if facet_fields:
        search_kwargs["facet"] = "true"
        search_kwargs["facet.field"] = facet_fields

    def _run_search() -> pysolr.Results:
        solr = pysolr.Solr(
            f"{client.base_url}/{collection}",
            timeout=client.config.connection_timeout,
        )
        return solr.search(q, **search_kwargs)

    try:
        results = await asyncio.to_thread(_run_search)
        formatted = client.response_formatter.format_search_results(results, start)
        if isinstance(formatted, str):
            return json.loads(formatted)
        return formatted
    except Exception as exc:
        raise QueryError(_remediation_hint(str(exc))) from exc
