"""WebSocket voice conversation endpoint."""
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import structlog

from backend.services.pipeline import VoicePipeline

router = APIRouter()
logger = structlog.get_logger("voice_ws")


@router.websocket("/voice")
async def voice_websocket(websocket: WebSocket):
    await websocket.accept()
    session_id = str(uuid.uuid4())
    pipeline = VoicePipeline(session_id=session_id)
    
    try:
        while True:
            data = await websocket.receive()
            
            if "bytes" in data:
                chunk = data["bytes"]
            elif "text" in data:
                chunk = data["text"].encode("utf-8")
            else:
                continue
            
            if len(chunk) == 0:
                result = await pipeline.process_end_of_utterance()
                if result:
                    await websocket.send_json({
                        "type": "transcript",
                        "text": result.transcript,
                        "language": result.language,
                    })
                    await websocket.send_json({
                        "type": "response",
                        "text": result.agent_response,
                        "intent": result.intent,
                    })
                    await websocket.send_json({
                        "type": "audio",
                        "base64": result.audio_base64,
                    })
                    await websocket.send_json({
                        "type": "latency",
                        "stt_ms": result.latency.stt_ms,
                        "llm_ms": result.latency.llm_ms,
                        "tts_ms": result.latency.tts_ms,
                        "total_ms": result.latency.total_ms,
                    })
            else:
                pipeline.append_audio(chunk)
                
    except WebSocketDisconnect:
        logger.info("websocket_disconnected", session_id=session_id)
    except Exception as e:
        logger.exception("websocket_error", session_id=session_id, error=str(e))
        await websocket.close(code=1011)
