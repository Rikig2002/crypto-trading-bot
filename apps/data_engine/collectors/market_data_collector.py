import logging
import signal
import threading

from apps.data_engine.services.market_data_service import MarketDataService
from config.settings import settings


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


class MarketDataCollector:
    def __init__(
        self,
        symbols: list[str] | None = None,
        timeframe: str | None = None,
        interval_seconds: int | None = None,
        batch_size: int | None = None,
    ):
        configured_symbols = [
            symbol.strip().upper()
            for symbol in settings.market_symbols.split(",")
            if symbol.strip()
        ]

        self.symbols = symbols or configured_symbols
        self.timeframe = timeframe or settings.market_timeframe
        self.interval_seconds = (
            interval_seconds
            if interval_seconds is not None
            else settings.collection_interval_seconds
        )
        self.batch_size = (
            batch_size
            if batch_size is not None
            else settings.market_batch_size
        )

        if not self.symbols:
            raise ValueError("At least one market symbol must be configured")

        self.service = MarketDataService()
        self.running = True
        self.stop_event = threading.Event()

        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)

    def _shutdown(self, signum, frame):
        logger.info("Shutdown signal received. Stopping collector...")
        self.running = False
        self.stop_event.set()

    def run_once(self) -> int:
        total_stored = 0

        for symbol in self.symbols:
            if not self.running:
                break

            try:
                stored = self.service.fetch_and_store(
                    symbol=symbol,
                    timeframe=self.timeframe,
                    limit=self.batch_size,
                )

                total_stored += stored

                logger.info(
                    "Market data collection completed | "
                    "symbol=%s | timeframe=%s | batch_size=%d | stored=%d",
                    symbol,
                    self.timeframe,
                    self.batch_size,
                    stored,
                )

            except Exception:
                logger.exception(
                    "Market data collection failed | "
                    "symbol=%s | timeframe=%s",
                    symbol,
                    self.timeframe,
                )

        return total_stored

    def run_forever(self) -> None:
        logger.info(
            "Starting market data collector | "
            "symbols=%s | timeframe=%s | interval=%ds | batch_size=%d",
            ",".join(self.symbols),
            self.timeframe,
            self.interval_seconds,
            self.batch_size,
        )

        while self.running:
            self.run_once()

            if self.running:
                self.stop_event.wait(self.interval_seconds)

        logger.info("Market data collector stopped.")


if __name__ == "__main__":
    MarketDataCollector().run_forever()
