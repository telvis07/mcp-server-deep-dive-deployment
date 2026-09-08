# mcp-server-deep-dive-deployment

Example [Model Context Protocol](https://modelcontextprotocol.io) servers, built while working
through the course below. The repo ships two of them — one over **stdio**, one over **streamable
HTTP** — so the two transports can be compared side by side. Both are packaged so they can be
installed and run directly from this GitHub repository, with no clone required.

> **Course:** [MCP Complete Guide – Build and Connect Tools for LLMs](https://learning.oreilly.com/course/mcp-complete-guide/9781806384136/) (O'Reilly)

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

## The streamable HTTP server

Stdio servers are launched by the client as a subprocess. A streamable HTTP server is the opposite:
it has to already be listening, and the client dials a URL. That makes it the transport you want
once the server lives in a container, on a PaaS, or anywhere across a network.

### Endpoint

```
http://127.0.0.1:8000/mcp
```

The path is `/mcp`, not `/` — that default comes from `streamable_http_path`. **Nothing is mounted
at the root**, so pointing a client at `http://127.0.0.1:8000` gets you:

```
INFO: 127.0.0.1:63946 - "POST / HTTP/1.1" 404 Not Found
```

If you see that 404, the path is missing from your URL. Skip the trailing slash too — `/mcp/`
answers with a 307 redirect.

### Configuration

| Variable | Default     | Purpose                                             |
| -------- | ----------- | --------------------------------------------------- |
| `HOST`   | `127.0.0.1` | Interface to bind. Set `0.0.0.0` in a container.     |
| `PORT`   | `8000`      | Port to bind. Hosting platforms usually inject this. |

```bash
HOST=0.0.0.0 PORT=9000 uv run mcpserver-http
```

### Connecting the MCP Inspector

The Inspector's `mcp dev` mode only speaks stdio, so for this server start it yourself first, then
attach the standalone Inspector:

```bash
uv run mcpserver-http                      # terminal 1
npx @modelcontextprotocol/inspector@latest # terminal 2
```

In the Inspector UI set **Transport Type** to `Streamable HTTP` and **URL** to
`http://127.0.0.1:8000/mcp`, then Connect.

For the stdio server, `mcp dev` handles the launching for you:

```bash
uv run mcp dev src/mcp_server_deep_dive_deployment/deployment.py
```

## Install from GitHub

Because the project defines console script entry points, `uvx` can build and run either server
straight from the repo. Nothing needs to be published to PyPI.

Verify it works end to end — swap the trailing script name to pick a server:

```bash
uvx --from git+https://github.com/telvis07/mcp-server-deep-dive-deployment mcpserver
uvx --from git+https://github.com/telvis07/mcp-server-deep-dive-deployment mcpserver-http
```

To pin a specific commit, tag, or branch, append it to the URL —
`git+https://github.com/telvis07/mcp-server-deep-dive-deployment@main`. Without a ref, `uvx` tracks
the default branch, and it caches builds: pass `--refresh` to pick up new commits.

## Connecting a client

The two servers are registered differently, because stdio is launched and HTTP is dialed.

### Claude Code

```bash
# stdio — Claude Code launches it
claude mcp add demo -- uvx --from git+https://github.com/telvis07/mcp-server-deep-dive-deployment mcpserver

# streamable HTTP — start the server first, then point at the URL
claude mcp add --transport http demo-http http://127.0.0.1:8000/mcp
```

### Claude Desktop

Add to `claude_desktop_config.json` and restart Claude Desktop. Both entries can live side by side:

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
    },
    "demo-http": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "http://127.0.0.1:8000/mcp"
      ]
    }
  }
}
```

`demo` is the whole story for stdio: Claude Desktop runs `uvx`, which builds from GitHub and speaks
MCP over the subprocess pipes.

`demo-http` needs the extra hop. Claude Desktop's config launches commands, so a remote server is
reached through the [`mcp-remote`](https://www.npmjs.com/package/mcp-remote) bridge, which Claude
Desktop starts over stdio and which forwards to the HTTP endpoint. **The server must already be
running** — `uv run mcpserver-http` in its own terminal — or the bridge has nothing to connect to.

> Claude Code talks to HTTP servers natively via `--transport http`, so it needs no bridge there.

#### Why not Settings → Connectors?

Claude's **Add custom connector** dialog rejects anything that is not `https`:

```
http://127.0.0.1:8000/mcp
⚠ URL must start with 'https'
```

A local server has no certificate, so the Connectors UI is not an option during development —
`mcp-remote` is. The bridge runs as a stdio subprocess and speaks plain HTTP to the server, so no
TLS is involved.

If you later want to connect a *deployed* server through Connectors, note that binding to localhost
turns on DNS-rebinding protection, which only accepts `Host` headers matching `127.0.0.1:*`,
`localhost:*`, or `[::1]:*`:

```
Host: 127.0.0.1:8000    -> 200
Host: abc123.ngrok.app  -> 421 Misdirected Request
```

So a plain tunnel gets refused. Either rewrite the forwarded header
(`ngrok http 8000 --host-header=rewrite`) or pass explicit `allowed_hosts` via
`TransportSecuritySettings`.

## Tools

| Tool       | Signature                       | `mcpserver` | `mcpserver-http` | Description                                        |
| ---------- | ------------------------------- | :---------: | :--------------: | -------------------------------------------------- |
| `add`      | `add(x: int, y: int) -> int`    |      ✅      |        ✅         | Sums 2 numbers.                                     |
| `count_to` | `count_to(n: int) -> str`       |      —      |        ✅         | Counts to n, streaming a progress update per step.  |
| `greeting` | `greeting(name: str) -> str`    |      —      |        ✅         | Send a greeting.                                    |

`count_to` is the one that shows why streamable HTTP exists: the client receives progress
notifications while the call is still running, instead of one lump of output at the end.

## Verify the install

Once a server is registered, ask the client to list its tools and check them against the table
above: `mcpserver` should offer `add` alone, `mcpserver-http` all three.

Then call a couple:

- `add(x=2, y=3)` returns `5` on either server.
- `greeting(name="Telvis")` returns `Hi Telvis` on the HTTP server.
- `count_to(n=5)` returns `Counted to 5.` and emits 5 progress notifications before it finishes.

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
