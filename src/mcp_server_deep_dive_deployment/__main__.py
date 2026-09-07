from mcp_server_deep_dive_deployment.deployment import mcp
import logging
import sys

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def main():
    logger.info("Starting mcp server")
    try:
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Interrupted, shutting down")
        return 130
    finally:
        logger.info("Stopping mcp server")
    return 0

if __name__ == "__main__":
    sys.exit(main())