from mcp.server.mcpserver import MCPServer
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

mcp = MCPServer("Demo")

@mcp.tool()
def add(x:int, y:int) -> int:
    """
    Sums 2 numbers.

    :param x:
    :param y:
    :return:
    """
    logger.info("Adding %s + %s", x, y)
    return x+y

if __name__ == '__main__':
    mcp.run()