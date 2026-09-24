import logging
import signal
import threading

from apps.data_engine.services.market_data_service import MarketDataService


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


class MarketDataCollector:
    def __init__(
        self,
        symbol: str = "BTCUSDT",
        timeframe: str = "1m",
        interval_seconds: int = 60,
    ):
        self.symbol = symbol
        self.timeframe = timeframe
        self.interval_seconds = interval_seconds

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
        stored = self.service.fetch_and_store(
            symbol=self.symbol,
            timeframe=self.timeframe,
            limit=5,
        )

        logger.info(
            "Market data collection completed | symbol=%s | timeframe=%s | stored=%d",
            self.symbol,
            self.timeframe,
            stored,
        )

        return stored

    def run_forever(self) -> None:
        logger.info(
            "Starting market data collector | symbol=%s | timeframe=%s",
            self.symbol,
            self.timeframe,
        )

        while self.running:
            try:
                self.run_once()
            except Exception:
                logger.exception("Market data collection failed")

            if self.running:
                self.stop_event.wait(self.interval_seconds)

        logger.info("Market data collector stopped.")


if __name__ == "__main__":
    MarketDataCollector().run_forever()
