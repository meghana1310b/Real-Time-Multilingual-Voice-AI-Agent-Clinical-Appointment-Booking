"""Persistent memory: Redis or in-memory fallback when Redis unavailable."""
import json
import asyncio

from backend.config import get_settings

_settings = get_settings()
PREFIX = "patient:"

_memory_store: dict[str, str] = {}
_memory_lock = asyncio.Lock()
_redis_client = None


def _use_memory() -> bool:
    return _settings.REDIS_URL.startswith("memory://")


def _get_redis():
    global _redis_client
    if _redis_client is None:
        import redis.asyncio as redis
        _redis_client = redis.from_url(_settings.REDIS_URL, decode_responses=True)
    return _redis_client


async def get_patient(patient_id: str) -> dict:
    if _use_memory():
        async with _memory_lock:
            key = f"{PREFIX}{patient_id}"
            if key not in _memory_store:
                return {}
            try:
                return json.loads(_memory_store[key])
            except json.JSONDecodeError:
                return {}
    client = _get_redis()
    key = f"{PREFIX}{patient_id}"
    data = await client.get(key)
    if not data:
        return {}
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        return {}


async def set_patient(patient_id: str, data: dict) -> None:
    if _use_memory():
        async with _memory_lock:
            _memory_store[f"{PREFIX}{patient_id}"] = json.dumps(data)
        return
    client = _get_redis()
    key = f"{PREFIX}{patient_id}"
    await client.set(key, json.dumps(data), ex=86400 * 365)


async def update_patient(patient_id: str, updates: dict) -> dict:
    current = await get_patient(patient_id)
    current.update(updates)
    await set_patient(patient_id, current)
    return current
