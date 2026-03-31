"""
Session store — Redis if available, in-memory fallback.
Stores CVSession objects keyed by session_id.
"""
import json
import logging
from typing import Optional
from backend.core.schema import CVSession

logger = logging.getLogger(__name__)


class InMemorySessionStore:
    def __init__(self):
        self._store: dict[str, dict] = {}

    async def get(self, session_id: str) -> Optional[CVSession]:
        data = self._store.get(session_id)
        if data is None:
            return None
        return CVSession.model_validate(data)

    async def set(self, session: CVSession) -> None:
        self._store[session.session_id] = session.model_dump()

    async def delete(self, session_id: str) -> None:
        self._store.pop(session_id, None)


class RedisSessionStore:
    def __init__(self, redis_url: str, ttl: int = 3600):
        import redis.asyncio as aioredis
        self._redis = aioredis.from_url(redis_url, decode_responses=True)
        self._ttl = ttl
        self._prefix = "cv_session:"

    async def get(self, session_id: str) -> Optional[CVSession]:
        raw = await self._redis.get(f"{self._prefix}{session_id}")
        if raw is None:
            return None
        return CVSession.model_validate(json.loads(raw))

    async def set(self, session: CVSession) -> None:
        key = f"{self._prefix}{session.session_id}"
        await self._redis.set(key, session.model_dump_json(), ex=self._ttl)

    async def delete(self, session_id: str) -> None:
        await self._redis.delete(f"{self._prefix}{session_id}")


def create_session_store(redis_url: Optional[str] = None, ttl: int = 3600):
    if redis_url:
        try:
            store = RedisSessionStore(redis_url, ttl)
            logger.info("Using Redis session store")
            return store
        except Exception as e:
            logger.warning(f"Redis unavailable ({e}), falling back to in-memory store")
    logger.info("Using in-memory session store")
    return InMemorySessionStore()


async def get_or_create_session(store, session_id: str) -> CVSession:
    session = await store.get(session_id)
    if session is None:
        session = CVSession(session_id=session_id)
        await store.set(session)
    return session
