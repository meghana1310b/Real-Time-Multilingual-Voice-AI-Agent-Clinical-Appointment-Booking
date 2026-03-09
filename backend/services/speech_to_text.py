"""Speech-to-Text service using OpenAI Whisper."""
import io
from typing import Optional

from openai import AsyncOpenAI

from backend.config import get_settings

_settings = get_settings()
_client: Optional[AsyncOpenAI] = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        kw = {"api_key": _settings.OPENAI_API_KEY}
        if _settings.OPENAI_API_BASE:
            kw["base_url"] = _settings.OPENAI_API_BASE
        _client = AsyncOpenAI(**kw)
    return _client


async def transcribe(audio_bytes: bytes) -> str:
    if not audio_bytes:
        return ""
    
    client = _get_client()
    buffer = io.BytesIO(audio_bytes)
    buffer.name = "audio.webm"
    
    transcript = await client.audio.transcriptions.create(
        model=_settings.STT_MODEL,
        file=buffer,
        response_format="text",
        language=None,
    )
    
    return (transcript if isinstance(transcript, str) else getattr(transcript, "text", "")) or ""
