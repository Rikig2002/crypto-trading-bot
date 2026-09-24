from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from apps.data_engine.database import SessionLocal
from apps.data_engine.models.trading import MarketData


TIMEFRAME_MINUTES = {
    "1m": 1,
    "3m": 3,
    "5m": 5,
    "15m": 15,
    "30m": 30,
    "1h": 60,
    "4h": 240,
    "1d": 1440,
}


class MarketDataQualityMonitor:
    def get_latest_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100,
    ) -> list[MarketData]:
        with SessionLocal() as session:
            return list(
                session.scalars(
                    select(MarketData)
                    .where(
                        MarketData.symbol == symbol,
                        MarketData.timeframe == timeframe,
                    )
                    .order_by(MarketData.timestamp.desc())
                    .limit(limit)
                ).all()
            )

    def check_continuity(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100,
    ) -> list[datetime]:
        if timeframe not in TIMEFRAME_MINUTES:
            raise ValueError(f"Unsupported timeframe: {timeframe}")

        rows = self.get_latest_candles(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )

        if len(rows) < 2:
            return []

        timestamps = sorted(
            row.timestamp.astimezone(timezone.utc)
            for row in rows
        )

        expected_gap = timedelta(
            minutes=TIMEFRAME_MINUTES[timeframe]
        )

        missing = []

        for previous, current in zip(
            timestamps,
            timestamps[1:],
        ):
            next_expected = previous + expected_gap

            while next_expected < current:
                missing.append(next_expected)
                next_expected += expected_gap

        return missing

    def check_recent_continuity(
        self,
        symbol: str,
        timeframe: str,
        recent_candles: int = 10,
    ) -> list[datetime]:
        return self.check_continuity(
            symbol=symbol,
            timeframe=timeframe,
            limit=recent_candles,
        )

    def get_status(
        self,
        symbol: str,
        timeframe: str,
        recent_candles: int = 10,
        max_staleness_minutes: int | None = None,
    ) -> dict:
        if timeframe not in TIMEFRAME_MINUTES:
            raise ValueError(f"Unsupported timeframe: {timeframe}")

        missing = self.check_recent_continuity(
            symbol=symbol,
            timeframe=timeframe,
            recent_candles=recent_candles,
        )

        latest = self.get_latest_candles(
            symbol=symbol,
            timeframe=timeframe,
            limit=1,
        )

        latest_timestamp = None

        if latest:
            latest_timestamp = latest[0].timestamp.astimezone(
                timezone.utc
            )

        now = datetime.now(timezone.utc)

        if max_staleness_minutes is None:
            max_staleness_minutes = TIMEFRAME_MINUTES[timeframe] * 2

        stale = False

        if latest_timestamp is None:
            stale = True
        else:
            age = now - latest_timestamp
            stale = age > timedelta(minutes=max_staleness_minutes)

        if stale:
            status = "STALE"
        elif missing:
            status = "DEGRADED"
        else:
            status = "HEALTHY"

        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "status": status,
            "latest_timestamp": latest_timestamp,
            "missing_count": len(missing),
            "missing_timestamps": missing,
            "stale": stale,
        }
