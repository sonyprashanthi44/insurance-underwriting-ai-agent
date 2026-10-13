from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_ENV = Path(__file__).resolve().parents[2] / ".env"
LOCAL_ENV = Path(".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(ROOT_ENV), str(LOCAL_ENV)),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    secret_key: str = "dev-secret-change-me"
    access_token_expire_minutes: int = 480
    database_url: str = "sqlite:///./underwriting.db"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    demo_user_email: str = "underwriter@demo.com"
    demo_user_password: str = "Demo@1234"

    @property
    def origins(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
