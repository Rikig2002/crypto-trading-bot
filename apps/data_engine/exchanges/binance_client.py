import requests


class BinanceClient:
    BASE_URL = "https://api.binance.com"

    def get_ticker(self, symbol: str = "BTCUSDT") -> dict:
        response = requests.get(
            f"{self.BASE_URL}/api/v3/ticker/price",
            params={"symbol": symbol},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def get_klines(
        self,
        symbol: str = "BTCUSDT",
        interval: str = "1m",
        limit: int = 100,
    ) -> list:
        response = requests.get(
            f"{self.BASE_URL}/api/v3/klines",
            params={
                "symbol": symbol,
                "interval": interval,
                "limit": limit,
            },
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
