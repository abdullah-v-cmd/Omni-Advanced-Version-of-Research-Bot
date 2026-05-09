"""
OmniSynth - Redis Client
Async Redis client for caching, sessions, and real-time features
"""
import json
from typing import Any, Optional
from loguru import logger

try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from app.core.config import settings


class RedisClient:
    def __init__(self):
        self.client = None
        self._connected = False

    async def connect(self):
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available")
            return
        try:
            self.client = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
            )
            await self.client.ping()
            self._connected = True
            logger.info("Redis connected successfully")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            self._connected = False

    async def disconnect(self):
        if self.client:
            await self.client.aclose()
            self._connected = False

    async def get(self, key: str) -> Optional[Any]:
        if not self._connected or not self.client:
            return None
        try:
            value = await self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.warning(f"Redis GET error: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        if not self._connected or not self.client:
            return False
        try:
            await self.client.setex(key, ttl, json.dumps(value, default=str))
            return True
        except Exception as e:
            logger.warning(f"Redis SET error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        if not self._connected or not self.client:
            return False
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Redis DELETE error: {e}")
            return False

    async def exists(self, key: str) -> bool:
        if not self._connected or not self.client:
            return False
        try:
            return bool(await self.client.exists(key))
        except Exception:
            return False

    async def publish(self, channel: str, message: Any) -> bool:
        if not self._connected or not self.client:
            return False
        try:
            await self.client.publish(channel, json.dumps(message, default=str))
            return True
        except Exception as e:
            logger.warning(f"Redis PUBLISH error: {e}")
            return False

    async def lpush(self, key: str, value: Any, ttl: int = 86400):
        if not self._connected or not self.client:
            return
        try:
            await self.client.lpush(key, json.dumps(value, default=str))
            await self.client.expire(key, ttl)
        except Exception as e:
            logger.warning(f"Redis LPUSH error: {e}")

    async def lrange(self, key: str, start: int = 0, end: int = -1):
        if not self._connected or not self.client:
            return []
        try:
            items = await self.client.lrange(key, start, end)
            return [json.loads(i) for i in items]
        except Exception as e:
            logger.warning(f"Redis LRANGE error: {e}")
            return []

    @property
    def is_connected(self):
        return self._connected


redis_client = RedisClient()
