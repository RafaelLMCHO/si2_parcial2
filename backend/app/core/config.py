from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "FashionStore API"
    api_prefix: str = "/api/v1"
    database_url: str = "postgresql://postgres:postgres@127.0.0.1:5434/fashionstore"
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 30
    refresh_token_days: int = 7
    verification_token_minutes: int = 60 * 24
    frontend_origin: str = "http://localhost:4200,http://127.0.0.1:4200"
    audit_enabled: bool = True
    trusted_proxies: str = ""
    expose_verification_token: bool = True
    email_backend: str = "console"


@lru_cache
def get_settings() -> Settings:
    return Settings()
