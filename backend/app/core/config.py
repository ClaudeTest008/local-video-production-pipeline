"""Application settings. Everything overridable via environment / .env."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="LVPP_", extra="ignore")

    app_name: str = "Local Video Production Pipeline"
    host: str = "127.0.0.1"
    port: int = 8321
    # Tauri app origins (tauri://localhost on macOS/Linux,
    # http(s)://tauri.localhost on Windows WebView2)
    cors_origins: list[str] = [
        "tauri://localhost",
        "http://tauri.localhost",
        "https://tauri.localhost",
    ]
    # Any localhost port — the web dev server may not get :3000
    cors_origin_regex: str = r"http://(localhost|127\.0\.0\.1):\d+"

    # SQLite default (local-first); set LVPP_DATABASE_URL for PostgreSQL.
    database_url: str = "sqlite:///./data/studio.db"

    # Root folder where per-project asset trees are created.
    projects_root: Path = Path("./data/projects")
    log_dir: Path = Path("./data/logs")

    # External services (all optional, all local-first defaults)
    comfyui_url: str = "http://127.0.0.1:8188"
    ollama_url: str = "http://127.0.0.1:11434"
    lmstudio_url: str = "http://127.0.0.1:1234/v1"

    # Cloud provider keys (optional; prefer OS keychain / env, never committed)
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    gemini_api_key: str = ""
    openrouter_api_key: str = ""
    brave_api_key: str = ""
    tavily_api_key: str = ""

    default_chat_provider: str = "ollama"
    default_chat_model: str = "llama3.1"

    # Quality review loop: Creative Director critiques key artifacts before they
    # advance; the producing agent revises on a REVISE verdict. Costs extra LLM
    # calls per reviewed stage — disable with LVPP_PIPELINE_REVIEW=false.
    pipeline_review: bool = True

    # Per-render wait budget in the pipeline's video stage (video models are slow)
    render_timeout_s: int = 1800

    def model_post_init(self, __context: object) -> None:
        # Tauri launches the backend with an arbitrary cwd, so the default
        # relative paths ("./data/...") would resolve differently per launch —
        # the DB and asset trees must land in the same place every time. Anchor
        # them to the backend root. Absolute overrides (env / PostgreSQL) pass
        # through untouched.
        root = Path(__file__).resolve().parents[2]
        prefix = "sqlite:///"
        if self.database_url.startswith(prefix):
            raw = self.database_url[len(prefix) :]
            if raw and not raw.startswith(":memory:") and not Path(raw).is_absolute():
                anchored = (root / raw.lstrip("./\\")).resolve()
                self.database_url = prefix + anchored.as_posix()
        if not self.projects_root.is_absolute():
            self.projects_root = root / self.projects_root
        if not self.log_dir.is_absolute():
            self.log_dir = root / self.log_dir


settings = Settings()
