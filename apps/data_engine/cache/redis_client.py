import redis

from config.settings import settings


redis_client = redis.Redis.from_url(
    settings.redis_url,
    decode_responses=True,
)


def check_redis() -> bool:
    return bool(redis_client.ping())
