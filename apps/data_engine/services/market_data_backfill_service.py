from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from apps.data_engine.database import SessionLocal
from apps.data_engine.exchanges.binance_client import BinanceClient
from apps.data_engine.models.trading import MarketData
from apps.data_engine.validators.market_data_validator import MarketDataValidator


class MarketDataBackfillService:
    def __init__(self):
        self.exchange = BinanceClient()

    def find_missing_timestamps(
        self,
        symbol: str,
        timeframe: str,
    ) -> list[datetime]:
        with SessionLocal() as session:
            rows = session.scalars(
                select(MarketData.timestamp)
                .where(
                    MarketData.symbol == symbol,
                    MarketData.timeframe == timeframe,
                )
                .order_by(MarketData.timestamp)
            ).all()

        if len(rows) < 2:
            return []

        step = self._timeframe_delta(timeframe)
        missing = []

        current = rows[0]
        existing = set(rows)

        while current < rows[-1]:
            if current not in existing:
                missing.append(current)
            current += step

        return missing

    def backfill(
        self,
        symbol: str,
        timeframe: str,
    ) -> int:
        missing = self.find_missing_timestamps(symbol, timeframe)

        if not missing:
            return 0

        start_time = min(missing)
        end_time = max(missing)

        interval_ms = int(
            self._timeframe_delta(timeframe).total_seconds() * 1000
        )

        candles = self.exchange.get_klines(
            symbol=symbol,
            interval=timeframe,
            start_time=int(start_time.timestamp() * 1000),
            end_time=int(end_time.timestamp() * 1000) + interval_ms,
            limit=1000,
        )

        stored = 0

        with SessionLocal() as session:
            existing = {
                row.timestamp
                for row in session.scalars(
                    select(MarketData).where(
                        MarketData.symbol == symbol,
                        MarketData.timeframe == timeframe,
                    )
                ).all()
            }

            for candle in candles:
                timestamp = datetime.fromtimestamp(
                    candle[0] / 1000,
                    tz=timezone.utc,
                )

                if timestamp in existing:
                    continue

                MarketDataValidator.validate(
                    symbol,
                    timeframe,
                    timestamp,
                    float(candle[1]),
                    float(candle[2]),
                    float(candle[3]),
                    float(candle[4]),
                    float(candle[5]),
                )

                session.add(
                    MarketData(
                        symbol=symbol,
                        timeframe=timeframe,
                        timestamp=timestamp,
                        open=float(candle[1]),
                        high=float(candle[2]),
                        low=float(candle[3]),
                        close=float(candle[4]),
                        volume=float(candle[5]),
                    )
                )

                stored += 1

            session.commit()

        return stored

    @staticmethod
    def _timeframe_delta(timeframe: str) -> timedelta:
        if timeframe.endswith("m"):
            return timedelta(minutes=int(timeframe[:-1]))

        if timeframe.endswith("h"):
            return timedelta(hours=int(timeframe[:-1]))

        if timeframe.endswith("d"):
            return timedelta(days=int(timeframe[:-1]))

        raise ValueError(f"Unsupported timeframe: {timeframe}")
