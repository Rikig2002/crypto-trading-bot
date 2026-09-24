from datetime import datetime, timedelta, timezone

from apps.data_engine.quality.market_data_quality import (
    MarketDataQualityMonitor,
    TIMEFRAME_MINUTES,
)


def test_timeframe_minutes():
    assert TIMEFRAME_MINUTES["1m"] == 1
    assert TIMEFRAME_MINUTES["5m"] == 5
    assert TIMEFRAME_MINUTES["1h"] == 60


def test_check_continuity_empty_when_not_enough_data():
    monitor = MarketDataQualityMonitor()

    monitor.get_latest_candles = lambda symbol, timeframe, limit: []

    result = monitor.check_continuity(
        symbol="BTCUSDT",
        timeframe="1m",
    )

    assert result == []


def test_check_continuity_detects_missing_candle():
    monitor = MarketDataQualityMonitor()

    now = datetime.now(timezone.utc).replace(second=0, microsecond=0)

    candles = [
        type("Candle", (), {"timestamp": now - timedelta(minutes=2)})(),
        type("Candle", (), {"timestamp": now})(),
    ]

    monitor.get_latest_candles = lambda symbol, timeframe, limit: candles

    result = monitor.check_continuity(
        symbol="BTCUSDT",
        timeframe="1m",
    )

    assert result == [now - timedelta(minutes=1)]


def test_check_continuity_returns_no_missing_for_continuous_data():
    monitor = MarketDataQualityMonitor()

    now = datetime.now(timezone.utc).replace(second=0, microsecond=0)

    candles = [
        type("Candle", (), {"timestamp": now - timedelta(minutes=2)})(),
        type("Candle", (), {"timestamp": now - timedelta(minutes=1)})(),
        type("Candle", (), {"timestamp": now})(),
    ]

    monitor.get_latest_candles = lambda symbol, timeframe, limit: candles

    result = monitor.check_continuity(
        symbol="BTCUSDT",
        timeframe="1m",
    )

    assert result == []


def test_get_status_marks_missing_data_as_degraded():
    monitor = MarketDataQualityMonitor()

    now = datetime.now(timezone.utc).replace(second=0, microsecond=0)

    candles = [
        type("Candle", (), {"timestamp": now - timedelta(minutes=2)})(),
        type("Candle", (), {"timestamp": now})(),
    ]

    monitor.get_latest_candles = lambda symbol, timeframe, limit: candles

    result = monitor.get_status(
        symbol="BTCUSDT",
        timeframe="1m",
        recent_candles=10,
        max_staleness_minutes=10,
    )

    assert result["status"] == "DEGRADED"
    assert result["stale"] is False
    assert result["missing_count"] == 1


def test_get_status_marks_old_data_as_stale():
    monitor = MarketDataQualityMonitor()

    old_timestamp = (
        datetime.now(timezone.utc)
        - timedelta(minutes=10)
    ).replace(second=0, microsecond=0)

    candles = [
        type("Candle", (), {"timestamp": old_timestamp})(),
    ]

    monitor.get_latest_candles = lambda symbol, timeframe, limit: candles

    result = monitor.get_status(
        symbol="BTCUSDT",
        timeframe="1m",
        recent_candles=10,
        max_staleness_minutes=2,
    )

    assert result["status"] == "STALE"
    assert result["stale"] is True


def test_get_status_marks_missing_latest_data_as_stale():
    monitor = MarketDataQualityMonitor()

    monitor.get_latest_candles = lambda symbol, timeframe, limit: []

    result = monitor.get_status(
        symbol="BTCUSDT",
        timeframe="1m",
    )

    assert result["status"] == "STALE"
    assert result["stale"] is True


def test_invalid_timeframe_raises_error():
    monitor = MarketDataQualityMonitor()

    monitor.get_latest_candles = lambda symbol, timeframe, limit: []

    try:
        monitor.get_status(
            symbol="BTCUSDT",
            timeframe="2m",
        )
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "Unsupported timeframe" in str(exc)
