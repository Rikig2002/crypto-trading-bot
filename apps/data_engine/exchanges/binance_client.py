import time

import requests


class BinanceClient:
    BASE_URL = "https://api.binance.com"

    def __init__(
        self,
        timeout: int = 10,
        max_retries: int = 3,
        backoff_seconds: float = 1.0,
    ):
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds
        self.session = requests.Session()

    def _get(self, path: str, params: dict) -> dict | list:
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.get(
                    f"{self.BASE_URL}{path}",
                    params=params,
                    timeout=self.timeout,
                )

                response.raise_for_status()
                return response.json()

            except requests.RequestException as exc:
                last_error = exc

                if attempt >= self.max_retries:
                    break

                delay = self.backoff_seconds * (2 ** attempt)
                time.sleep(delay)

        raise RuntimeError(
            f"Binance API request failed after "
            f"{self.max_retries + 1} attempts"
        ) from last_error

    def get_ticker(self, symbol: str = "BTCUSDT") -> dict:
        return self._get(
            "/api/v3/ticker/price",
            {"symbol": symbol},
        )

    def get_klines(
        self,
        symbol: str = "BTCUSDT",
        interval: str = "1m",
        limit: int = 100,
    ) -> list:
        return self._get(
            "/api/v3/klines",
            {
                "symbol": symbol,
                "interval": interval,
                "limit": limit,
            },
        )
