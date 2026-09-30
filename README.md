# Solr MCP

A Python package for accessing Apache Solr indexes via Model Context Protocol (MCP). This integration allows AI assistants like Claude to perform powerful search queries against your Solr indexes, combining both keyword and vector search capabilities.

## Features

- **MCP Server**: Implements the Model Context Protocol for integration with AI assistants
- **Hybrid Search**: Combines keyword search precision with vector search semantic understanding
- **Vector Embeddings**: Generates embeddings for documents using Ollama with nomic-embed-text
- **Unified Collections**: Store both document content and vector embeddings in the same collection
- **Docker Integration**: Easy setup with Docker and docker-compose
- **Optimized Vector Search**: Efficiently handles combined vector and SQL queries by pushing down SQL filters to the vector search stage, ensuring optimal performance even with large result sets and pagination

## Architecture

### Vector Search Optimization

The system employs an important optimization for combined vector and SQL queries. When executing a query that includes both vector similarity search and SQL filters:

1. SQL filters (WHERE clauses) are pushed down to the vector search stage
2. This ensures that vector similarity calculations are only performed on documents that will match the final SQL criteria
3. Significantly improves performance for queries with:
   - Selective WHERE clauses
   - Pagination (LIMIT/OFFSET)
   - Large result sets

This optimization reduces computational overhead and network transfer by minimizing the number of vector similarity calculations needed.

## Quick Start

1. Clone this repository
2. Start SolrCloud with Docker:
   ```bash
   docker-compose up -d
   ```
3. Install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install uv
   uv sync
   ```
4. Process and index the sample document:
   ```bash
   python scripts/process_markdown.py data/bitcoin-whitepaper.md --output data/processed/bitcoin_sections.json
   python scripts/create_unified_collection.py unified
   python scripts/unified_index.py data/processed/bitcoin_sections.json --collection unified
   ```
5. Run the MCP server (stdio transport, for local MCP clients):
   ```bash
   uv run run-server
   ```

For more detailed setup and usage instructions, see the [QUICKSTART.md](QUICKSTART.md) guide.

## MCP client configuration

The server speaks MCP over **stdio** by default. Install and run it from Git with [uv](https://docs.astral.sh/uv/):

### Install from GitHub (recommended)

```json
{
  "mcpServers": {
    "solr-mcp-server": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/kevinbtalbert/solr-mcp-python-stdio@main",
        "run-server"
      ],
      "env": {
        "SOLR_BASE_URL": "https://solr-app.yoururlhere.ylcu-atmi.cloudera.site/solr",
        "MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

Use this block in Cursor MCP settings, Claude Desktop, or Agent Studio MCP configuration.

Set **`SOLR_BASE_URL`** to your Solr Admin base URL (including the `/solr` path). The server uses plain HTTP/HTTPS with no login or API keys—suitable for open Solr endpoints. ZooKeeper is **not** required: when `ZOOKEEPER_HOSTS` is unset, collections are discovered through Solr’s HTTP API. For local SolrCloud with ZK directly reachable, optionally set `ZOOKEEPER_HOSTS` to a comma-separated list (e.g. `localhost:2181`).

### MCP tools (Agent Studio / Claude)

| Tool | Use for |
|------|---------|
| `list-collections` | Discover collection names |
| `get-schema` | Field names and types before querying |
| `search` | **Primary** — Lucene `/select` (full text, filters, facets, sort) |
| `sql-select` | Solr SQL when you need it explicitly |
| `semantic-select` / `vector-select` | SQL + vector similarity (requires embeddings setup) |
| `get-default-text-vectorizer` | Embedding model dimensions for semantic search |

After changing this repo, refresh the MCP server (restart the host or bump the git ref) so clients pick up new tool names. No `mcp` or ZooKeeper parameters are required in tool calls.

### Local checkout

```json
{
  "mcpServers": {
    "solr-mcp-server": {
      "command": "uvx",
      "args": [
        "--from",
        "file:///absolute/path/to/solr-mcp-python-stdio",
        "run-server"
      ],
      "env": {
        "SOLR_BASE_URL": "https://your-solr-host.example.com/solr"
      }
    }
  }
}
```

### Transport

Set `MCP_TRANSPORT` to choose how the server connects to the client:

| Value | Use case |
|-------|----------|
| `stdio` (default) | Cursor, Claude Desktop, and other subprocess-based MCP hosts |
| `sse` | HTTP/SSE deployment (e.g. `run-server --transport sse --port 8000`) |

## Requirements

- Python 3.10 or higher
- Docker and Docker Compose
- SolrCloud 9.x
- Ollama (for embedding generation)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.