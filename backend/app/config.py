from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    app_name: str = "Smart CRM API"
    database_url: str = f"sqlite:///{(BASE_DIR / 'smart_crm.db').as_posix()}"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    cors_origin_regex: str = r"^https?://(localhost|127\.0\.0\.1):[0-9]+$"
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_vision_model: str = ""
    llm_timeout_seconds: float = 12.0

    model_config = SettingsConfigDict(
        env_prefix="SMART_CRM_",
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
