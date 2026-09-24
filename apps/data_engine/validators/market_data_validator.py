from datetime import datetime, timezone
from math import isfinite


class MarketDataValidator:
    """Validates OHLCV market candles before database storage."""

    @staticmethod
    def validate(
        symbol: str,
        timeframe: str,
        timestamp: datetime,
        open_price: float,
        high: float,
        low: float,
        close: float,
        volume: float,
    ) -> None:
        if not symbol:
            raise ValueError("Symbol cannot be empty")

        if not timeframe:
            raise ValueError("Timeframe cannot be empty")

        if timestamp.tzinfo is None:
            raise ValueError("Timestamp must be timezone-aware")

        if timestamp.tzinfo != timezone.utc:
            timestamp = timestamp.astimezone(timezone.utc)

        prices = {
            "open": open_price,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        }

        for name, value in prices.items():
            if not isfinite(value):
                raise ValueError(f"{name} must be finite")

        if open_price <= 0:
            raise ValueError("Open price must be positive")

        if high <= 0:
            raise ValueError("High price must be positive")

        if low <= 0:
            raise ValueError("Low price must be positive")

        if close <= 0:
            raise ValueError("Close price must be positive")

        if volume < 0:
            raise ValueError("Volume cannot be negative")

        if high < low:
            raise ValueError("High price cannot be lower than low price")

        if high < open_price or high < close:
            raise ValueError("High price must be >= open and close")

        if low > open_price or low > close:
            raise ValueError("Low price must be <= open and close")
