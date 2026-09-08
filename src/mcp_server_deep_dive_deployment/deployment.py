"""Demo server, served over stdio.

Stdio is the transport to reach for when the client launches the server itself
as a subprocess, which is how `claude mcp add` and claude_desktop_config.json
work by default.
"""

import logging

from mcp.server.mcpserver import MCPServer

from mcp_server_deep_dive_deployment.runner import serve

logger = logging.getLogger(__name__)

mcp = MCPServer("Demo")


@mcp.tool()
def add(x: int, y: int) -> int:
    """Sums 2 numbers.

    :param x: the first addend
    :param y: the second addend
    :return: the sum of x and y
    """
    logger.info("Adding %s + %s", x, y)
    return x + y


def main() -> int:
    return serve(mcp)


if __name__ == "__main__":
    raise SystemExit(main())
