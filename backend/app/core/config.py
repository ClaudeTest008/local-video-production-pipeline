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


settings = Settings()
