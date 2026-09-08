"""Entry point for `python -m mcp_server_deep_dive_deployment`.

Defaults to the stdio Demo server. The streamable HTTP server has its own
console script; see the README.
"""

from mcp_server_deep_dive_deployment.deployment import main

if __name__ == "__main__":
    raise SystemExit(main())
