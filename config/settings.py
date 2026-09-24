from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "crypto-trading-bot"
    environment: str = "development"
    debug: bool = True

    database_url: str = "sqlite:///./data/bot.db"
    redis_url: str = "redis://localhost:6379/0"

    exchange_name: str = "binance"
    exchange_api_key: str = ""
    exchange_api_secret: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
