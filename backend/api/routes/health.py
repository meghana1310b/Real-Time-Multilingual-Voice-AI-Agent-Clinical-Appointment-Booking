"""Health check endpoints."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "running", "service": "2care-voice-ai-agent"}
