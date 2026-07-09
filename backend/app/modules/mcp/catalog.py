"""Known MCP servers. Adding one = adding a dict entry (or a DB row via the API) —
no core code changes. env values marked <required> must be filled in Settings.
"""

CATALOG: list[dict] = [
    {
        "name": "filesystem",
        "description": "Read/write files in allowed directories",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "{projects_root}"],
        "env": {},
    },
    {
        "name": "git",
        "description": "Local git operations",
        "command": "uvx",
        "args": ["mcp-server-git"],
        "env": {},
    },
    {
        "name": "github",
        "description": "GitHub repos, PRs, issues",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-github"],
        "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "<required>"},
    },
    {
        "name": "python",
        "description": "Run Python code in a sandbox",
        "command": "uvx",
        "args": ["mcp-run-python"],
        "env": {},
    },
    {
        "name": "sqlite",
        "description": "Query local SQLite databases",
        "command": "uvx",
        "args": ["mcp-server-sqlite", "--db-path", "{db_path}"],
        "env": {},
    },
    {
        "name": "docker",
        "description": "Manage Docker containers",
        "command": "uvx",
        "args": ["mcp-server-docker"],
        "env": {},
    },
    {
        "name": "playwright",
        "description": "Browser automation",
        "command": "npx",
        "args": ["-y", "@playwright/mcp@latest"],
        "env": {},
    },
    {
        "name": "brave-search",
        "description": "Web search via Brave",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-brave-search"],
        "env": {"BRAVE_API_KEY": "<required>"},
    },
    {
        "name": "comfyui",
        "description": "Drive a local ComfyUI instance",
        "command": "uvx",
        "args": ["comfyui-mcp"],
        "env": {"COMFYUI_URL": "http://127.0.0.1:8188"},
    },
    {
        "name": "ffmpeg",
        "description": "Media processing via FFmpeg",
        "command": "uvx",
        "args": ["ffmpeg-mcp"],
        "env": {},
    },
    {
        "name": "whisper",
        "description": "Local speech-to-text",
        "command": "uvx",
        "args": ["whisper-mcp"],
        "env": {},
    },
    {
        "name": "browser",
        "description": "Headless browser fetch/read",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-puppeteer"],
        "env": {},
    },
    {
        "name": "local-rag",
        "description": "Query the local ChromaDB knowledge base",
        "command": "uvx",
        "args": ["chroma-mcp"],
        "env": {"CHROMA_PATH": "{data_dir}/chroma"},
    },
]
