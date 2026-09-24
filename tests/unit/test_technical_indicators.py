import numpy as np
import pandas as pd
import pytest

from apps.data_engine.features.technical_indicators import TechnicalIndicators


def close_series():
    return pd.Series(
        [100, 101, 102, 103, 102, 104, 105, 106, 107, 108],
        dtype=float,
    )


def ohlcv_dataframe(rows=60):
    close = pd.Series(
        np.linspace(100, 160, rows),
        dtype=float,
    )

    return pd.DataFrame(
        {
            "open": close - 0.5,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
            "volume": np.full(rows, 1000.0),
        }
    )


def test_sma():
    close = close_series()

    result = TechnicalIndicators.sma(close, 3)

    assert result.iloc[:2].isna().all()
    assert result.iloc[2] == pytest.approx(101.0)
    assert result.iloc[3] == pytest.approx(102.0)


def test_ema():
    close = close_series()

    result = TechnicalIndicators.ema(close, 3)

    assert result.iloc[:2].isna().all()
    assert result.iloc[2] == pytest.approx(101.25)


def test_rsi():
    close = pd.Series(
        [100, 101, 102, 103, 104, 105, 106, 107, 108, 109],
        dtype=float,
    )

    result = TechnicalIndicators.rsi(close, 3)

    assert result.iloc[:3].isna().all()
    assert result.iloc[3] == pytest.approx(100.0)


def test_rsi_declining_market():
    close = pd.Series(
        [110, 109, 108, 107, 106, 105, 104],
        dtype=float,
    )

    result = TechnicalIndicators.rsi(close, 3)

    assert result.iloc[-1] == pytest.approx(0.0)


def test_macd_columns():
    close = pd.Series(
        np.linspace(100, 150, 60),
        dtype=float,
    )

    result = TechnicalIndicators.macd(close)

    assert list(result.columns) == [
        "macd",
        "macd_signal",
        "macd_histogram",
    ]

    assert len(result) == len(close)


def test_macd_invalid_periods():
    close = close_series()

    with pytest.raises(ValueError, match="fast_period must be smaller"):
        TechnicalIndicators.macd(
            close,
            fast_period=26,
            slow_period=12,
        )


def test_atr():
    high = pd.Series([11, 12, 13, 14, 15], dtype=float)
    low = pd.Series([9, 10, 11, 12, 13], dtype=float)
    close = pd.Series([10, 11, 12, 13, 14], dtype=float)

    result = TechnicalIndicators.atr(
        high,
        low,
        close,
        period=3,
    )

    assert result.iloc[:2].isna().all()
    assert result.iloc[2:].notna().all()


def test_bollinger_bands():
    close = pd.Series(
        [100, 101, 102, 103, 104, 105],
        dtype=float,
    )

    result = TechnicalIndicators.bollinger_bands(
        close,
        period=3,
        num_std=2.0,
    )

    assert list(result.columns) == [
        "bb_middle",
        "bb_upper",
        "bb_lower",
    ]

    assert result.iloc[:2].isna().all().all()
    assert result.iloc[2]["bb_middle"] == pytest.approx(101.0)
    assert result.iloc[2]["bb_upper"] > result.iloc[2]["bb_middle"]
    assert result.iloc[2]["bb_lower"] < result.iloc[2]["bb_middle"]


def test_returns():
    close = pd.Series(
        [100, 110, 99],
        dtype=float,
    )

    result = TechnicalIndicators.returns(close)

    assert pd.isna(result.iloc[0])
    assert result.iloc[1] == pytest.approx(0.10)
    assert result.iloc[2] == pytest.approx(-0.10)


def test_build_features():
    df = ohlcv_dataframe()

    result = TechnicalIndicators.build_features(df)

    expected_columns = {
        "open",
        "high",
        "low",
        "close",
        "volume",
        "return_1",
        "sma_20",
        "sma_50",
        "ema_12",
        "ema_26",
        "rsi_14",
        "macd",
        "macd_signal",
        "macd_histogram",
        "atr_14",
        "bb_middle",
        "bb_upper",
        "bb_lower",
    }

    assert expected_columns.issubset(result.columns)
    assert len(result) == len(df)


def test_build_features_missing_column():
    df = ohlcv_dataframe().drop(columns=["volume"])

    with pytest.raises(ValueError, match="Missing required columns"):
        TechnicalIndicators.build_features(df)


@pytest.mark.parametrize(
    "period",
    [0, -1, -10],
)
def test_invalid_period_rejected(period):
    close = close_series()

    with pytest.raises(ValueError, match="period must be positive"):
        TechnicalIndicators.sma(close, period)


@pytest.mark.parametrize(
    "period",
    [1.5, "14", True, False],
)
def test_non_integer_period_rejected(period):
    close = close_series()

    with pytest.raises(TypeError, match="period must be an integer"):
        TechnicalIndicators.sma(close, period)


def test_invalid_bollinger_std():
    close = close_series()

    with pytest.raises(ValueError, match="num_std must be positive"):
        TechnicalIndicators.bollinger_bands(
            close,
            period=3,
            num_std=0,
        )
