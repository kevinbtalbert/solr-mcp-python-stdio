"""FastMCP server implementation for Solr."""

import argparse
import functools
import logging
import os
import sys
from typing import List

from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.routing import Mount, Route

from solr_mcp.solr.client import SolrClient
from solr_mcp.solr.config import SolrConfig
from solr_mcp.tools import TOOLS_DEFINITION
from solr_mcp.tools._context import set_solr_client

load_dotenv()

logger = logging.getLogger(__name__)

DEFAULT_TRANSPORT = "stdio"
SUPPORTED_TRANSPORTS = ("stdio", "sse")


def parse_zookeeper_hosts(raw: str | None) -> List[str]:
    """Parse comma-separated ZooKeeper hosts; empty means HTTP-only Solr."""
    if raw is None or not raw.strip():
        return []
    return [host.strip() for host in raw.split(",") if host.strip()]


class SolrMCPServer:
    """Model Context Protocol server for SolrCloud integration."""

    def __init__(
        self,
        mcp_port: int = int(os.getenv("MCP_PORT", "8081")),
        solr_base_url: str = os.getenv("SOLR_BASE_URL", "http://localhost:8983/solr"),
        zookeeper_hosts: List[str] | None = None,
        connection_timeout: int = int(os.getenv("CONNECTION_TIMEOUT", "10")),
        transport: str = os.getenv("MCP_TRANSPORT", DEFAULT_TRANSPORT),
    ):
        """Initialize the server."""
        if transport not in SUPPORTED_TRANSPORTS:
            raise ValueError(
                f"Unsupported MCP transport {transport!r}; "
                f"expected one of {SUPPORTED_TRANSPORTS}"
            )

        self.port = mcp_port
        self.transport = transport
        if zookeeper_hosts is None:
            zookeeper_hosts = parse_zookeeper_hosts(os.getenv("ZOOKEEPER_HOSTS"))
        self.config = SolrConfig(
            solr_base_url=solr_base_url,
            zookeeper_hosts=zookeeper_hosts,
            connection_timeout=connection_timeout,
        )
        self._setup_server()

    def _setup_server(self):
        """Set up the MCP server and Solr client."""
        try:
            self._connect_to_solr()
        except Exception as e:
            logger.error("Solr connection error: %s", e)
            sys.exit(1)

        if self.transport == "sse":
            logger.info("MCP SSE server will listen on port %s", self.port)

        self.mcp = FastMCP(
            name="Solr MCP Server",
            instructions="""This server provides tools for interacting with Solr:
- list-collections: discover collections
- get-schema: field names and types for a collection
- search: Lucene /select queries (preferred for Q&A)
- sql-select, semantic-select, vector-select: Solr SQL (advanced)""",
            debug=True,
            port=self.port,
        )

        self._setup_tools()

    def _connect_to_solr(self):
        """Initialize Solr client connection."""
        self.solr_client = SolrClient(config=self.config)
        set_solr_client(self.solr_client)

    def _transform_tool_params(self, tool_name: str, params: dict) -> dict:
        """Transform tool parameters before they are passed to the tool."""
        if "mcp" in params:
            if isinstance(params["mcp"], str):
                params["mcp"] = self
        return params

    def _wrap_tool(self, tool):
        """Wrap a tool to handle parameter transformation."""

        @functools.wraps(tool)
        async def wrapper(*args, **kwargs):
            kwargs = self._transform_tool_params(tool.__name__, kwargs)
            return await tool(*args, **kwargs)

        wrapper._is_tool = True
        wrapper._tool_name = getattr(tool, "_tool_name", tool.__name__)
        wrapper._tool_description = tool.__doc__ if tool.__doc__ else ""

        return wrapper

    def _setup_tools(self):
        """Register MCP tools."""
        for tool_func in TOOLS_DEFINITION:
            wrapped_tool = self._wrap_tool(tool_func)
            tool_name = getattr(wrapped_tool, "_tool_name", None)
            if tool_name:
                self.mcp.tool(name=tool_name)(wrapped_tool)
            else:
                self.mcp.tool()(wrapped_tool)

    def run(self) -> None:
        """Run the SolrMCP server."""
        logger.info("Starting Solr MCP server (transport=%s)", self.transport)
        self.mcp.run(self.transport)

    async def close(self):
        """Clean up resources."""
        if hasattr(self.solr_client, "close"):
            await self.solr_client.close()
        if hasattr(self.mcp, "close"):
            await self.mcp.close()


def create_starlette_app(mcp_server: Server, *, debug: bool = False) -> Starlette:
    """Create a Starlette application that can serve the provided MCP server with SSE."""
    sse = SseServerTransport("/messages/")

    async def handle_sse(request: Request) -> None:
        async with sse.connect_sse(
            request.scope,
            request.receive,
            request._send,  # noqa: SLF001
        ) as (read_stream, write_stream):
            await mcp_server.run(
                read_stream,
                write_stream,
                mcp_server.create_initialization_options(),
            )

    return Starlette(
        debug=debug,
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )


def _configure_logging(level: str) -> None:
    """Send logs to stderr so stdio transport can use stdout for MCP messages."""
    logging.basicConfig(
        level=getattr(logging, level),
        stream=sys.stderr,
        format="%(levelname)s %(name)s: %(message)s",
        force=True,
    )


def main() -> None:
    """Main entry point."""
    default_transport = os.getenv("MCP_TRANSPORT", DEFAULT_TRANSPORT)

    parser = argparse.ArgumentParser(description="Solr MCP Server")
    parser.add_argument(
        "--mcp-port",
        type=int,
        help="MCP server port (SSE mode)",
        default=int(os.getenv("MCP_PORT", "8081")),
    )
    parser.add_argument(
        "--solr-base-url",
        help="Solr base URL",
        default=os.getenv("SOLR_BASE_URL", "http://localhost:8983/solr"),
    )
    parser.add_argument(
        "--zookeeper-hosts",
        help=(
            "Optional ZooKeeper hosts (comma-separated). Omit for Solr HTTP-only "
            "(managed Solr / Solr at a single URL)."
        ),
        default=os.getenv("ZOOKEEPER_HOSTS", ""),
    )
    parser.add_argument(
        "--connection-timeout",
        type=int,
        help="Connection timeout in seconds",
        default=int(os.getenv("CONNECTION_TIMEOUT", "10")),
    )
    parser.add_argument(
        "--transport",
        choices=SUPPORTED_TRANSPORTS,
        default=default_transport,
        help="Transport mode (stdio or sse). Defaults to MCP_TRANSPORT env or stdio.",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (SSE mode only)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("MCP_SSE_PORT", "8000")),
        help="Port to listen on (SSE mode only)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=os.getenv("LOG_LEVEL", "INFO"),
        help="Set the logging level",
    )

    args = parser.parse_args()
    _configure_logging(args.log_level)

    server = SolrMCPServer(
        mcp_port=args.mcp_port,
        solr_base_url=args.solr_base_url,
        zookeeper_hosts=parse_zookeeper_hosts(args.zookeeper_hosts),
        connection_timeout=args.connection_timeout,
        transport=args.transport,
    )

    if args.transport == "stdio":
        server.run()
    else:
        mcp_server = server.mcp._mcp_server  # noqa: WPS437
        starlette_app = create_starlette_app(mcp_server, debug=True)
        import uvicorn

        uvicorn.run(starlette_app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
