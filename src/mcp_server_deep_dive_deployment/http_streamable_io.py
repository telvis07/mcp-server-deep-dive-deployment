"""Demo server, served over streamable HTTP.

Streamable HTTP is the transport to reach for when the server runs somewhere
the client cannot launch it as a subprocess — a container, a PaaS dyno, a box
on the other side of the network. The client connects to a URL instead of a
pipe, so the server has to already be listening.

The MCP endpoint is served at `/mcp`. Set HOST and PORT to override where it
binds; hosting platforms usually inject PORT for you.
"""

import asyncio
import logging
import os

from mcp.server.mcpserver import Context, MCPServer

from mcp_server_deep_dive_deployment.deployment import add
from mcp_server_deep_dive_deployment.runner import serve

logger = logging.getLogger(__name__)

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000

mcp = MCPServer("HTTP Streamable IO")

# Same implementation as the stdio server; registering it here keeps the two
# servers comparable without a second copy of the function.
mcp.tool()(add)


@mcp.tool()
async def count_to(n: int, ctx: Context) -> str:
    """Counts to n, streaming a progress update after each step.

    This is the part stdio cannot show off well: the client sees progress
    arrive over the open HTTP stream while the tool is still running, rather
    than waiting for one lump of output at the end.

    :param n: how high to count
    :param ctx: request context, injected by the server
    :return: a short summary of what was counted
    """
    for i in range(1, n + 1):
        await ctx.report_progress(progress=i, total=n, message=f"counted {i} of {n}")
        await asyncio.sleep(0.1)
    logger.info("Counted to %s", n)
    return f"Counted to {n}."


def main() -> int:
    return serve(
        mcp,
        transport="streamable-http",
        host=os.environ.get("HOST", DEFAULT_HOST),
        port=int(os.environ.get("PORT", DEFAULT_PORT)),
    )


if __name__ == "__main__":
    raise SystemExit(main())
