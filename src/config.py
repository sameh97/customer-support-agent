"""
src/config.py — single source of truth for all config.
Reads from .env automatically. Any value can be overridden
by an environment variable (important for Docker later).
"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):

    # ── LLM ──────────────────────────────────────────────────────────
    ollama_model: str       = Field("qwen2.5:3b", alias="OLLAMA_MODEL")
    ollama_base_url: str    = Field("http://localhost:11434", alias="OLLAMA_BASE_URL")
    temperature: float      = Field(0.2, alias="TEMPERATURE")

    # ── Business identity ─────────────────────────────────────────────
    business_name: str      = Field("Acme Corp", alias="BUSINESS_NAME")
    support_email: str      = Field("support@acmecorp.com", alias="SUPPORT_EMAIL")
    system_prompt: str      = Field(
        "You are a professional customer support assistant. "
        "Be concise, friendly, and helpful. "
        "Never make up information you don't know.",
        alias="SYSTEM_PROMPT",
    )

    # ── RAG ───────────────────────────────────────────────────────────
    chroma_dir: str         = Field("data/chroma_db", alias="CHROMA_DIR")
    docs_dir: str           = Field("data/docs", alias="DOCS_DIR")
    rag_top_k: int          = Field(5, alias="RAG_TOP_K")
    chunk_size: int         = Field(800, alias="CHUNK_SIZE")
    chunk_overlap: int      = Field(100, alias="CHUNK_OVERLAP")

    # ── Gmail ─────────────────────────────────────────────────────────
    gmail_credentials_path: str = Field("config/credentials.json", alias="GMAIL_CREDENTIALS_PATH")
    gmail_token_path: str       = Field("config/token.json", alias="GMAIL_TOKEN_PATH")

    # ── LangGraph ─────────────────────────────────────────────────────
    default_thread_id: str  = Field("session-1", alias="DEFAULT_THREAD_ID")
    max_tool_iterations: int = Field(5, alias="MAX_TOOL_ITERATIONS")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "populate_by_name": True,   # allow both alias and field name
    }


# Single instance — import this everywhere
settings = Settings()