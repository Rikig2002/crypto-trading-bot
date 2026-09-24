from datetime import datetime, timezone
from math import inf, nan

import pytest

from apps.data_engine.validators.market_data_validator import MarketDataValidator


def valid_candle():
    return {
        "symbol": "BTCUSDT",
        "timeframe": "1m",
        "timestamp": datetime.now(timezone.utc),
        "open_price": 100.0,
        "high": 110.0,
        "low": 90.0,
        "close": 105.0,
        "volume": 1000.0,
    }


def test_valid_candle_passes():
    MarketDataValidator.validate(**valid_candle())


def test_empty_symbol_rejected():
    data = valid_candle()
    data["symbol"] = ""

    with pytest.raises(ValueError, match="Symbol cannot be empty"):
        MarketDataValidator.validate(**data)


def test_empty_timeframe_rejected():
    data = valid_candle()
    data["timeframe"] = ""

    with pytest.raises(ValueError, match="Timeframe cannot be empty"):
        MarketDataValidator.validate(**data)


def test_naive_timestamp_rejected():
    data = valid_candle()
    data["timestamp"] = datetime.now()

    with pytest.raises(
        ValueError,
        match="Timestamp must be timezone-aware",
    ):
        MarketDataValidator.validate(**data)


@pytest.mark.parametrize(
    "field",
    [
        "open_price",
        "high",
        "low",
        "close",
        "volume",
    ],
)
@pytest.mark.parametrize("invalid_value", [nan, inf, -inf])
def test_non_finite_values_rejected(field, invalid_value):
    data = valid_candle()
    data[field] = invalid_value

    with pytest.raises(ValueError, match=f"{field.replace('_', ' ')} must be finite"):
        MarketDataValidator.validate(**data)


@pytest.mark.parametrize(
    "field",
    [
        "open_price",
        "high",
        "low",
        "close",
    ],
)
def test_non_positive_prices_rejected(field):
    data = valid_candle()
    data[field] = 0.0

    expected_messages = {
        "open_price": "Open price must be positive",
        "high": "High price must be positive",
        "low": "Low price must be positive",
        "close": "Close price must be positive",
    }

    with pytest.raises(ValueError, match=expected_messages[field]):
        MarketDataValidator.validate(**data)


def test_negative_volume_rejected():
    data = valid_candle()
    data["volume"] = -1.0

    with pytest.raises(ValueError, match="Volume cannot be negative"):
        MarketDataValidator.validate(**data)


def test_high_lower_than_low_rejected():
    data = valid_candle()
    data["high"] = 80.0
    data["low"] = 90.0

    with pytest.raises(
        ValueError,
        match="High price cannot be lower than low price",
    ):
        MarketDataValidator.validate(**data)


def test_high_lower_than_open_rejected():
    data = valid_candle()
    data["high"] = 95.0
    data["open_price"] = 100.0

    with pytest.raises(
        ValueError,
        match="High price must be >= open and close",
    ):
        MarketDataValidator.validate(**data)


def test_high_lower_than_close_rejected():
    data = valid_candle()
    data["high"] = 100.0
    data["close"] = 105.0

    with pytest.raises(
        ValueError,
        match="High price must be >= open and close",
    ):
        MarketDataValidator.validate(**data)


def test_low_higher_than_open_rejected():
    data = valid_candle()
    data["low"] = 105.0
    data["open_price"] = 100.0

    with pytest.raises(
        ValueError,
        match="Low price must be <= open and close",
    ):
        MarketDataValidator.validate(**data)


def test_low_higher_than_close_rejected():
    data = valid_candle()
    data["low"] = 106.0
    data["close"] = 105.0

    with pytest.raises(
        ValueError,
        match="Low price must be <= open and close",
    ):
        MarketDataValidator.validate(**data)


def test_zero_volume_is_allowed():
    data = valid_candle()
    data["volume"] = 0.0

    MarketDataValidator.validate(**data)


def test_utc_timestamp_passes():
    data = valid_candle()
    data["timestamp"] = datetime(
        2026,
        9,
        24,
        15,
        0,
        tzinfo=timezone.utc,
    )

    MarketDataValidator.validate(**data)
