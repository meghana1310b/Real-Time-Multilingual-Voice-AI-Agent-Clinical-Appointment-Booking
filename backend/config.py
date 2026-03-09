"""Application configuration."""
from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment."""
    
    APP_ENV: str = Field(default="development")
    CORS_ALLOW_ORIGINS: str = Field(default="*")
    
    # Database: use sqlite:///./voice_ai.db for no-Docker local dev
    DATABASE_URL: str = Field(
        default="sqlite:///./voice_ai.db"
    )
    
    # Redis: use memory:// for no-Docker local dev (in-memory fallback)
    REDIS_URL: str = Field(default="memory://")
    REDIS_SESSION_TTL: int = Field(default=3600)
    
    # OpenAI
    OPENAI_API_KEY: str | None = Field(default=None)
    OPENAI_API_BASE: str | None = Field(default=None)
    LLM_MODEL: str = Field(default="gpt-4o-mini")
    STT_MODEL: str = Field(default="whisper-1")
    TTS_MODEL: str = Field(default="tts-1")
    TTS_VOICE: str = Field(default="alloy")
    
    # Latency
    LATENCY_TARGET_MS: int = Field(default=450)
    LATENCY_LOG_ENABLED: bool = Field(default=True)
    
    def cors_origins_list(self) -> List[str]:
        if self.CORS_ALLOW_ORIGINS == "*":
            return ["*"]
        return [o.strip() for o in self.CORS_ALLOW_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
