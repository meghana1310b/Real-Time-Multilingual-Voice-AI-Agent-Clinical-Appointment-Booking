"""Session memory: Redis or in-memory fallback when Redis unavailable."""
import json
import asyncio
import time

from backend.config import get_settings

_settings = get_settings()
PREFIX = "session:"

# In-memory fallback when REDIS_URL is memory://
_memory_store: dict[str, tuple[str, float]] = {}
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


async def get_session(session_id: str) -> dict:
    if _use_memory():
        async with _memory_lock:
            key = f"{PREFIX}{session_id}"
            if key not in _memory_store:
                return _initialize_session()
            data, _ = _memory_store[key]
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                return _initialize_session()
    client = _get_redis()
    key = f"{PREFIX}{session_id}"
    data = await client.get(key)
    if not data:
        return _initialize_session()
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        return _initialize_session()


async def set_session(session_id: str, data: dict) -> None:
    if _use_memory():
        async with _memory_lock:
            key = f"{PREFIX}{session_id}"
            _memory_store[key] = (json.dumps(data), time.time() + _settings.REDIS_SESSION_TTL)
        return
    client = _get_redis()
    key = f"{PREFIX}{session_id}"
    await client.set(key, json.dumps(data), ex=_settings.REDIS_SESSION_TTL)


async def update_session(session_id: str, updates: dict) -> dict:
    current = await get_session(session_id)
    current.update(updates)
    await set_session(session_id, current)
    return current


async def append_message(session_id: str, role: str, content: str) -> None:
    data = await get_session(session_id)
    messages = data.get("messages", [])
    messages.append({"role": role, "content": content})
    data["messages"] = messages[-20:]
    await set_session(session_id, data)


def _initialize_session() -> dict:
    """Initialize a new session with default structure."""
    return {
        "messages": [],
        "language": None,
        "patient_name": None,
        "doctor": None,
        "preferred_date": None,
        "preferred_time": None,
        "visit_reason": None,
        "appointment_status": None,  # new | reschedule | cancel | check_availability
        "intent": None,
        "patient_phone": None,
        "created_at": time.time(),
        "last_updated": time.time(),
    }


async def get_session_summary(session_id: str) -> dict:
    """Get a summary of collected patient information."""
    session = await get_session(session_id)
    return {
        "patient_name": session.get("patient_name"),
        "doctor": session.get("doctor"),
        "preferred_date": session.get("preferred_date"),
        "preferred_time": session.get("preferred_time"),
        "visit_reason": session.get("visit_reason"),
        "appointment_status": session.get("appointment_status"),
        "language": session.get("language"),
        "intent": session.get("intent"),
        "message_count": len(session.get("messages", [])),
    }
