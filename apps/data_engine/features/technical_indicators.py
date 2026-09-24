import numpy as np
import pandas as pd


class TechnicalIndicators:
    """Calculate technical indicators from OHLCV market data."""

    @staticmethod
    def sma(series: pd.Series, period: int) -> pd.Series:
        TechnicalIndicators._validate_period(period)
        return series.rolling(window=period, min_periods=period).mean()

    @staticmethod
    def ema(series: pd.Series, period: int) -> pd.Series:
        TechnicalIndicators._validate_period(period)
        return series.ewm(
            span=period,
            adjust=False,
            min_periods=period,
        ).mean()

    @staticmethod
    def rsi(close: pd.Series, period: int = 14) -> pd.Series:
        TechnicalIndicators._validate_period(period)

        delta = close.diff()

        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.ewm(
            alpha=1 / period,
            adjust=False,
            min_periods=period,
        ).mean()

        avg_loss = loss.ewm(
            alpha=1 / period,
            adjust=False,
            min_periods=period,
        ).mean()

        rs = avg_gain / avg_loss

        rsi = 100 - (100 / (1 + rs))

        # When there is no loss, RSI is conventionally 100.
        rsi = rsi.where(avg_loss != 0, 100.0)

        return rsi

    @staticmethod
    def macd(
        close: pd.Series,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
    ) -> pd.DataFrame:
        TechnicalIndicators._validate_period(fast_period)
        TechnicalIndicators._validate_period(slow_period)
        TechnicalIndicators._validate_period(signal_period)

        if fast_period >= slow_period:
            raise ValueError("fast_period must be smaller than slow_period")

        fast_ema = TechnicalIndicators.ema(close, fast_period)
        slow_ema = TechnicalIndicators.ema(close, slow_period)

        macd_line = fast_ema - slow_ema

        signal_line = macd_line.ewm(
            span=signal_period,
            adjust=False,
            min_periods=signal_period,
        ).mean()

        histogram = macd_line - signal_line

        return pd.DataFrame(
            {
                "macd": macd_line,
                "macd_signal": signal_line,
                "macd_histogram": histogram,
            },
            index=close.index,
        )

    @staticmethod
    def atr(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14,
    ) -> pd.Series:
        TechnicalIndicators._validate_period(period)

        previous_close = close.shift(1)

        true_range = pd.concat(
            [
                high - low,
                (high - previous_close).abs(),
                (low - previous_close).abs(),
            ],
            axis=1,
        ).max(axis=1)

        return true_range.ewm(
            alpha=1 / period,
            adjust=False,
            min_periods=period,
        ).mean()

    @staticmethod
    def bollinger_bands(
        close: pd.Series,
        period: int = 20,
        num_std: float = 2.0,
    ) -> pd.DataFrame:
        TechnicalIndicators._validate_period(period)

        if num_std <= 0:
            raise ValueError("num_std must be positive")

        middle = close.rolling(
            window=period,
            min_periods=period,
        ).mean()

        std = close.rolling(
            window=period,
            min_periods=period,
        ).std()

        upper = middle + (num_std * std)
        lower = middle - (num_std * std)

        return pd.DataFrame(
            {
                "bb_middle": middle,
                "bb_upper": upper,
                "bb_lower": lower,
            },
            index=close.index,
        )

    @staticmethod
    def returns(close: pd.Series) -> pd.Series:
        return close.pct_change()

    @staticmethod
    def build_features(df: pd.DataFrame) -> pd.DataFrame:
        required_columns = {"open", "high", "low", "close", "volume"}

        missing = required_columns - set(df.columns)

        if missing:
            raise ValueError(
                f"Missing required columns: {sorted(missing)}"
            )

        result = df.copy()

        result["return_1"] = TechnicalIndicators.returns(result["close"])
        result["sma_20"] = TechnicalIndicators.sma(result["close"], 20)
        result["sma_50"] = TechnicalIndicators.sma(result["close"], 50)
        result["ema_12"] = TechnicalIndicators.ema(result["close"], 12)
        result["ema_26"] = TechnicalIndicators.ema(result["close"], 26)
        result["rsi_14"] = TechnicalIndicators.rsi(result["close"], 14)

        macd = TechnicalIndicators.macd(result["close"])
        result = result.join(macd)

        result["atr_14"] = TechnicalIndicators.atr(
            result["high"],
            result["low"],
            result["close"],
            14,
        )

        bollinger = TechnicalIndicators.bollinger_bands(
            result["close"],
            20,
            2.0,
        )
        result = result.join(bollinger)

        return result

    @staticmethod
    def _validate_period(period: int) -> None:
        if not isinstance(period, int) or isinstance(period, bool):
            raise TypeError("period must be an integer")

        if period <= 0:
            raise ValueError("period must be positive")
