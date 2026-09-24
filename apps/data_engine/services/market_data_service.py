from datetime import datetime, timezone

from sqlalchemy import select

from apps.data_engine.database import SessionLocal
from apps.data_engine.exchanges.binance_client import BinanceClient
from apps.data_engine.models.trading import MarketData
from apps.data_engine.validators.market_data_validator import MarketDataValidator


class MarketDataService:
    def __init__(self):
        self.exchange = BinanceClient()

    def fetch_and_store(
        self,
        symbol: str = "BTCUSDT",
        timeframe: str = "1m",
        limit: int = 100,
    ) -> int:
        candles = self.exchange.get_klines(
            symbol=symbol,
            interval=timeframe,
            limit=limit,
        )

        stored = 0

        with SessionLocal() as session:
            for candle in candles:
                timestamp = datetime.fromtimestamp(
                    candle[0] / 1000,
                    tz=timezone.utc,
                )

                existing = session.scalar(
                    select(MarketData).where(
                        MarketData.symbol == symbol,
                        MarketData.timeframe == timeframe,
                        MarketData.timestamp == timestamp,
                    )
                )

                if existing:
                    continue

                open_price = float(candle[1])
                high = float(candle[2])
                low = float(candle[3])
                close = float(candle[4])
                volume = float(candle[5])

                MarketDataValidator.validate(
                    symbol=symbol,
                    timeframe=timeframe,
                    timestamp=timestamp,
                    open_price=open_price,
                    high=high,
                    low=low,
                    close=close,
                    volume=volume,
                )

                market_data = MarketData(
                    symbol=symbol,
                    timeframe=timeframe,
                    timestamp=timestamp,
                    open=open_price,
                    high=high,
                    low=low,
                    close=close,
                    volume=volume,
                )

                session.add(market_data)
                stored += 1

            session.commit()

        return stored
