from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "The Portfolia"
    app_env: str = "development"
    debug: bool = True
    secret_key: str = "change-me-in-production"
    admin_registration_key: str | None = None
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    database_url: str = "sqlite:///./the_portfolia.db"
    postgres_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/the_portfolia"
    cors_origins: str = (
        "http://localhost:3000,http://localhost:8080,"
        "http://127.0.0.1:3000,http://127.0.0.1:8080,"
        "http://0.0.0.0:3000,http://0.0.0.0:8080"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
