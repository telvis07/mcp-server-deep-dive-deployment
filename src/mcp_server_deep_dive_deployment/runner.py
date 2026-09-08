"""Shared startup plumbing for every server in this package.

Each server module owns its tools and nothing else; the logging setup, the
lifecycle messages, and the Ctrl-C handling all live here so they only exist
once.
"""

import logging
from typing import Any, Literal

from mcp.server.mcpserver import MCPServer

logger = logging.getLogger(__name__)

Transport = Literal["stdio", "sse", "streamable-http"]


def serve(server: MCPServer, transport: Transport = "stdio", **run_kwargs: Any) -> int:
    """Run an MCP server until it stops, and report a process exit code.

    :param server: the configured MCPServer to run
    :param transport: which MCP transport to serve on
    :param run_kwargs: transport-specific options forwarded to MCPServer.run()
    :return: 0 on a clean shutdown, 130 if interrupted with Ctrl-C
    """
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting %s server on %s transport", server.name, transport)
    try:
        server.run(transport, **run_kwargs)
    except KeyboardInterrupt:
        logger.info("Interrupted, shutting down")
        return 130
    finally:
        logger.info("Stopping %s server", server.name)
    return 0
