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

## Servers

The repo ships two servers so the two transports can be compared side by side. Each one is a
separate console script; a client talks to one or the other, never both at once.

| Script           | Module                  | Transport         | Use it when                                        |
| ---------------- | ----------------------- | ----------------- | -------------------------------------------------- |
| `mcpserver`      | `deployment.py`         | stdio             | the client launches the server as a subprocess      |
| `mcpserver-http` | `http_streamable_io.py` | streamable HTTP   | the server already runs somewhere and you dial a URL |

## Run the servers

**stdio** — running it directly just waits for a client on stdin/stdout. That's expected, not a
hang:

```bash
uv run mcpserver
```

**streamable HTTP** — this one listens, so you can curl it or point a client at the URL. It serves
MCP at `/mcp` on `127.0.0.1:8000`; set `HOST` and `PORT` to move it:

```bash
uv run mcpserver-http
# -> http://127.0.0.1:8000/mcp

PORT=9000 uv run mcpserver-http
```

To poke at the tools interactively instead, use the MCP Inspector:

```bash
uv run mcp dev src/mcp_server_deep_dive_deployment/deployment.py
```

## Install from GitHub

Because the project defines console script entry points, `uvx` can build and run either server
straight from the repo. Nothing needs to be published to PyPI.

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

Swap the trailing `mcpserver` for `mcpserver-http` to run the HTTP server the same way. To pin a
specific commit, tag, or branch, append it to the URL —
`git+https://github.com/telvis07/mcp-server-deep-dive-deployment@main`. Without a ref, `uvx` tracks
the default branch, and it caches builds: pass `--refresh` to pick up new commits.

## Tools

| Tool       | Signature                         | Server        | Description                                    |
| ---------- | --------------------------------- | ------------- | ---------------------------------------------- |
| `add`      | `add(x: int, y: int) -> int`      | both          | Sums 2 numbers.                                 |
| `count_to` | `count_to(n: int) -> str`         | HTTP only     | Counts to n, streaming a progress update per step. |

`count_to` is the one that shows why streamable HTTP exists: the client receives progress
notifications while the call is still running, instead of one lump of output at the end.

## Verify the install

Once a server is registered, ask the client to list its tools. Every tool in the table above should
show up for that server — `add(x=2, y=3)` should return `5`, and against the HTTP server
`count_to(n=5)` should emit 5 progress notifications before returning.

## Project layout

```
src/mcp_server_deep_dive_deployment/
├── __init__.py
├── __main__.py             # `python -m ...`, defaults to the stdio server
├── runner.py               # shared serve(): logging, lifecycle, Ctrl-C handling
├── deployment.py           # MCPServer("Demo") over stdio
└── http_streamable_io.py   # MCPServer("HTTP Streamable IO") over streamable HTTP
```

Startup plumbing lives once in `runner.py`, so a server module is just its tools plus a `main()`
that hands the server to `serve()`.

## Adding a tool

Tools are plain functions in a server module. Type hints define the input schema and the docstring
becomes the tool description the model reads, so both are worth getting right:

```python
@mcp.tool()
def multiply(x: int, y: int) -> int:
    """Multiplies 2 numbers."""
    return x * y
```

To share one tool across both servers, define it once and register it on the other with
`mcp.tool()(add)` — that is how `add` appears on both without a second copy.

Restart the client (or `--refresh` the `uvx` install) to pick up the change, and add a row to the
[Tools](#tools) table above so it stays the one place that lists what these servers expose.

## Adding a server

1. Add a module next to the existing ones with its own `MCPServer(...)` and tools.
2. Give it a `main()` that returns `serve(mcp, ...)` from `runner.py`.
3. Register a console script in `pyproject.toml` under `[project.scripts]`.

Clients then select it by name: `uvx --from git+https://github.com/telvis07/mcp-server-deep-dive-deployment <script>`.
