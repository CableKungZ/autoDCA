from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://dca:changeme@postgres:5432/autodca"
    redis_url: str = "redis://redis:6379/0"
    fernet_key: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    binance_api_key: str = ""
    binance_api_secret: str = ""
    bitkub_api_key: str = ""
    bitkub_api_secret: str = ""
    log_level: str = "INFO"
    run_mode: str = "api"

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
