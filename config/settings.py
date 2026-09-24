from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "crypto-trading-bot"
    environment: str = "development"
    debug: bool = True

    database_url: str = "postgresql+psycopg://crypto_user:change_me@localhost:5432/crypto_trading"
    redis_url: str = "redis://localhost:6379/0"

    exchange_name: str = "binance"
    exchange_api_key: str = ""
    exchange_api_secret: str = ""

    market_symbols: str = "BTCUSDT"
    market_timeframe: str = "1m"
    collection_interval_seconds: int = 60
    market_batch_size: int = 5

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
