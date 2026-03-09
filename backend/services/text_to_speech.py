"""Text-to-Speech service using OpenAI TTS."""
from typing import Optional

from openai import AsyncOpenAI

from backend.config import get_settings

_settings = get_settings()
_client: Optional[AsyncOpenAI] = None

LANG_TO_VOICE = {
    "en": "alloy",
    "hi": "nova",
    "ta": "shimmer",
}


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        kw = {"api_key": _settings.OPENAI_API_KEY}
        if _settings.OPENAI_API_BASE:
            kw["base_url"] = _settings.OPENAI_API_BASE
        _client = AsyncOpenAI(**kw)
    return _client


async def synthesize(text: str, language: str = "en") -> bytes:
    if not text.strip():
        return b""
    
    client = _get_client()
    voice = LANG_TO_VOICE.get(language, _settings.TTS_VOICE)
    
    response = await client.audio.speech.create(
        model=_settings.TTS_MODEL,
        voice=voice,
        input=text,
    )
    
    return response.content
