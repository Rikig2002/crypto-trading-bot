from fastapi import APIRouter

from apps.data_engine.cache.redis_client import check_redis

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/redis")
def redis_health():
    return {
        "status": "ok" if check_redis() else "error",
        "service": "redis",
    }
