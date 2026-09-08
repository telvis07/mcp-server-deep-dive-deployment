# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A teaching repo with two example MCP servers — one over **stdio**, one over **streamable HTTP** —
kept deliberately parallel so the transports can be compared. It is packaged so `uvx --from
git+https://github.com/telvis07/mcp-server-deep-dive-deployment <script>` works with no clone, which
is why the console scripts in `pyproject.toml` are load-bearing rather than a convenience.

## Commands

```bash
uv sync                    # create .venv/ and install from uv.lock
uv run mcpserver           # stdio server; blocks waiting on stdin/stdout (not a hang)
uv run mcpserver-http      # streamable HTTP at http://127.0.0.1:8000/mcp (HOST/PORT override)

uv run mcp dev src/mcp_server_deep_dive_deployment/deployment.py  # Inspector, stdio only
```

The Inspector's `mcp dev` speaks stdio only. For the HTTP server, start it yourself and attach the
standalone Inspector (`npx @modelcontextprotocol/inspector@latest`) with Transport Type
`Streamable HTTP` and URL `http://127.0.0.1:8000/mcp`.

There is no test suite, linter, or formatter configured. Don't invent commands for them.

## Deployment

`render.yaml` deploys `mcpserver-http` to Render's **native Python runtime** — not Docker. Don't
propose a Dockerfile; Render reads the existing `.python-version` (3.14) and the build installs from
`uv.lock` via `uv sync --frozen`. Keep `--frozen`: it is what makes deploys reproducible, and the
lockfile is committed for exactly that reason.

```bash
CI=true render blueprints validate    # validate render.yaml before pushing
```

Two settings look like oversights and are not:

- **No `healthCheckPath`.** Nothing is mounted at `/`, so a check there would 404 in a restart loop.
- **`startCommand` calls `./.venv/bin/mcpserver-http` directly**, not `uv run`, which would re-check
  the environment on every start and need `uv` on `PATH` at runtime.

`autoDeployTrigger: commit` means merging to `main` redeploys. Note `autoDeploy` and `env` are
deprecated Blueprint keys — use `autoDeployTrigger` and `runtime`.

Deployment needs no application code: `http_streamable_io.main()` already reads `HOST`/`PORT` from
the environment. Keep it that way rather than hardcoding Render specifics into the server module.

## Architecture

```
src/mcp_server_deep_dive_deployment/
├── __main__.py             # `python -m ...` → the stdio server
├── runner.py               # serve(): logging, lifecycle, Ctrl-C → exit 130
├── deployment.py           # MCPServer("Demo"), stdio
└── http_streamable_io.py   # MCPServer("HTTP Streamable IO"), streamable-http
```

`runner.serve(server, transport, **run_kwargs)` holds *all* startup plumbing. A server module is
therefore only its tools plus a `main()` that returns `serve(...)`. Put anything shared — logging
config, shutdown handling, new lifecycle concerns — in `runner.py`, never duplicated per server.

Tools are shared, not copied: `http_streamable_io.py` imports `add` from `deployment.py` and
registers it with `mcp.tool()(add)`. Follow that pattern for any tool that belongs on both servers.

`count_to` exists specifically to demonstrate streaming — it takes a `Context` and calls
`ctx.report_progress()` per step. Keep it async and keep the progress calls; that behavior is the
point of the HTTP server.

## API surface

This uses **mcp 2.2.0**, where the server class is `MCPServer` imported from `mcp.server.mcpserver`.
It is not the older `FastMCP`/`mcp.server.fastmcp` API — don't "correct" it to that. Python 3.14 is
required.

Tool signatures are the contract the model reads: type hints generate the input schema and the
docstring becomes the tool description. Existing tools use `:param:`/`:return:` reST style.

## Conventions

- The README's **Tools** table is the single place listing what each server exposes. Add a row when
  you add a tool.
- Adding a server means: new module with its own `MCPServer(...)`, a `main()` returning `serve(...)`,
  and a console script entry in `[project.scripts]`.
- Prose in the README documents *why* a transport or workaround exists (the `/mcp` path, the
  `mcp-remote` bridge for Claude Desktop, why the Connectors UI rejects `http://`). Preserve that
  reasoning when editing rather than trimming to bare steps.
