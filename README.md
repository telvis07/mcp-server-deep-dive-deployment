# mcp-server-deep-dive-deployment

An example [Model Context Protocol](https://modelcontextprotocol.io) server, built for the MCP
developer course. It exposes a single `add` tool and is packaged so it can be installed and run
directly from this GitHub repository — no clone required.

## Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/) 0.12.9 or newer
- Python 3.14 (uv will download it for you if it isn't already installed)

## Local setup

```bash
git clone https://github.com/telvis07/mcp-server-deep-dive-deployment.git
cd mcp-server-deep-dive-deployment
uv sync
```

`uv sync` creates `.venv/` and installs the locked dependencies from `uv.lock`.

## Run the server

The server speaks MCP over **stdio**, so running it directly just waits for a client on
stdin/stdout — that's expected, not a hang.

```bash
uv run mcpserver
```

To poke at the tools interactively instead, use the MCP Inspector:

```bash
uv run mcp dev src/mcp_server_deep_dive_deployment/deployment.py
```

## Install from GitHub

Because the project defines a `mcpserver` script entry point, `uvx` can build and run it straight
from the repo. Nothing needs to be published to PyPI.

Verify it works end to end:

```bash
uvx --from git+https://github.com/telvis07/mcp-server-deep-dive-deployment mcpserver
```

### Claude Code

```bash
claude mcp add demo -- uvx --from git+https://github.com/telvis07/mcp-server-deep-dive-deployment mcpserver
```

### Claude Desktop

Add this to `claude_desktop_config.json`, then restart Claude Desktop:

```json
{
  "mcpServers": {
    "demo": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/telvis07/mcp-server-deep-dive-deployment",
        "mcpserver"
      ]
    }
  }
}
```

To pin a specific commit, tag, or branch, append it to the URL —
`git+https://github.com/telvis07/mcp-server-deep-dive-deployment@v0.1.0`. Without a ref, `uvx`
tracks the default branch, and it caches builds: pass `--refresh` to pick up new commits.

## Tools

| Tool  | Signature                    | Description      |
| ----- | ---------------------------- | ---------------- |
| `add` | `add(x: int, y: int) -> int` | Sums 2 numbers.  |

## Verify the install

Once the server is registered, ask the client to list its tools. Every tool in the table above
should show up — for the current set, that means `add`, and `add(x=2, y=3)` should return `5`.

## Project layout

```
src/mcp_server_deep_dive_deployment/
├── __init__.py
├── __main__.py      # main(): entry point for the `mcpserver` script
└── deployment.py    # MCPServer instance and @mcp.tool() definitions
```

## Adding a tool

Tools are plain functions in `deployment.py`. Type hints define the input schema and the docstring
becomes the tool description, so both are worth getting right:

```python
@mcp.tool()
def multiply(x: int, y: int) -> int:
    """Multiplies 2 numbers."""
    return x * y
```

Restart the client (or `--refresh` the `uvx` install) to pick up the change, and add a row to the
[Tools](#tools) table above so it stays the one place that lists what this server exposes.
