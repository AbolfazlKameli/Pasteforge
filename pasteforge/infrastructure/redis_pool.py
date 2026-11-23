from redis import asyncio as redis

from pasteforge.core.config import configs

fastapi_redis_pool = redis.ConnectionPool.from_url(
    url=configs.REDIS_URL,
    max_connections=configs.REDIS_MAX_CONNECTIONS,
)

redis_conn = redis.Redis(connection_pool=fastapi_redis_pool)
