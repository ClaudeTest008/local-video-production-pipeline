# MCP Guide

Discovering, enabling, and exporting Model Context Protocol servers from LVPP — and adding your own without touching core code.

## What is MCP?

The [Model Context Protocol](https://modelcontextprotocol.io) is an open standard that lets AI applications (Claude Desktop, Cursor, agent frameworks) talk to external tools and data through small server processes with a uniform interface. LVPP acts as a **catalog and configuration manager** for MCP servers: it ships a curated list of servers useful for video production, stores your enabled set in the database, and exports a ready-to-paste `mcpServers` config for any MCP client. LVPP does not run the server processes itself — your MCP client does.

## The catalog

13 built-in entries (`backend/app/modules/mcp/catalog.py`):

| Name | Description | Launcher |
|---|---|---|
| `filesystem` | Read/write files in allowed directories | `npx @modelcontextprotocol/server-filesystem` |
| `git` | Local git operations | `uvx mcp-server-git` |
| `github` | GitHub repos, PRs, issues | `npx @modelcontextprotocol/server-github` |
| `python` | Run Python code in a sandbox | `uvx mcp-run-python` |
| `sqlite` | Query local SQLite databases | `uvx mcp-server-sqlite` |
| `docker` | Manage Docker containers | `uvx mcp-server-docker` |
| `playwright` | Browser automation | `npx @playwright/mcp` |
| `brave-search` | Web search via Brave | `npx @modelcontextprotocol/server-brave-search` |
| `comfyui` | Drive a local ComfyUI instance | `uvx comfyui-mcp` |
| `ffmpeg` | Media processing via FFmpeg | `uvx ffmpeg-mcp` |
| `browser` | Headless browser fetch/read | `npx @modelcontextprotocol/server-puppeteer` |
| `local-rag` | Query the local ChromaDB knowledge base | `uvx chroma-mcp` |

`npx`-based servers need Node ≥ 20; `uvx`-based servers need [uv](https://docs.astral.sh/uv/).

## Discover → toggle → export

**UI**: the **MCP** page (`http://localhost:3000/mcp`) has a *Discover* button, a toggle switch per server, and an *Export config* card with copy-to-clipboard.

**API** (base `http://127.0.0.1:8321/api`):

```bash
# Import every catalog entry not yet in your DB (all arrive disabled)
curl -X POST http://127.0.0.1:8321/api/mcp/discover
# {"added": ["filesystem", "git", ...], "total": 13}

# List registered servers
curl http://127.0.0.1:8321/api/mcp/servers

# Enable/disable one
curl -X POST http://127.0.0.1:8321/api/mcp/servers/3/toggle

# Export enabled servers as mcpServers JSON
curl http://127.0.0.1:8321/api/mcp/export
```

Also available: `GET /mcp/catalog` (raw catalog), `PATCH /mcp/servers/{id}` (edit command/args/env/enabled), `DELETE /mcp/servers/{id}`.

## The export format

`GET /api/mcp/export` returns only **enabled** servers in the standard `mcpServers` shape:

```json
{
  "mcpServers": {
    "git": { "command": "uvx", "args": ["mcp-server-git"], "env": {} },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": { "GITHUB_PERSONAL_ACCESS_TOKEN": "<required>" }
    }
  }
}
```

Consuming it:

- **Claude Desktop** — merge the `mcpServers` object into `claude_desktop_config.json` (Windows: `%APPDATA%\Claude\`, macOS: `~/Library/Application Support/Claude/`), then restart Claude Desktop.
- **Cursor** — merge into `.cursor/mcp.json` (per-project) or `~/.cursor/mcp.json` (global).

## Placeholders: fill before use

Catalog entries ship two kinds of placeholders that LVPP stores verbatim — replace them before handing the config to a client:

- **`<required>` env values** (`GITHUB_PERSONAL_ACCESS_TOKEN`, `BRAVE_API_KEY`): fill in your real token, either by `PATCH`-ing the server's `env` (see below) so the export is correct once and for all, or by editing the pasted JSON in the client config.
- **`{projects_root}` / `{db_path}` / `{data_dir}` path tokens** in `args` (used by `filesystem`, `sqlite`, `local-rag`): replace with real absolute paths on your machine, e.g. `C:\Users\you\lvpp\backend\data\projects`.

```bash
curl -X PATCH http://127.0.0.1:8321/api/mcp/servers/3 \
  -H "Content-Type: application/json" \
  -d '{"env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_yourtoken"}}'
```

Tokens live in your local database (`backend/data/studio.db`) — fine for a single-user local app, but do not commit or share exports containing them.

## Adding a custom server

Any MCP server can be registered at runtime — no catalog edit, no core changes:

```bash
curl -X POST http://127.0.0.1:8321/api/mcp/servers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "obsidian",
    "description": "Read my Obsidian vault",
    "command": "npx",
    "args": ["-y", "mcp-obsidian", "/path/to/vault"],
    "env": {},
    "enabled": true
  }'
```

Names must be unique (409 on duplicates). Custom servers are tagged `source: "custom"` and behave exactly like catalog ones: toggle, edit, export. To add an entry for everyone, a one-dict addition to `CATALOG` in `backend/app/modules/mcp/catalog.py` is all it takes.
