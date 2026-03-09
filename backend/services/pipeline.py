"""Voice pipeline: STT -> Language -> Agent -> TTS with latency logging."""
import base64
import time
from dataclasses import dataclass

from backend.services.speech_to_text import transcribe
from backend.services.language_detection import detect_language
from backend.services.text_to_speech import synthesize
from backend.agent.reasoning import handle_message
from backend.memory.session_memory import update_session
import structlog

logger = structlog.get_logger("pipeline")


@dataclass
class LatencyBreakdown:
    stt_ms: float
    llm_ms: float
    tts_ms: float
    total_ms: float


@dataclass
class PipelineResult:
    transcript: str
    language: str
    agent_response: str
    intent: str
    audio_base64: str
    latency: LatencyBreakdown


class VoicePipeline:
    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self._audio_buffer = bytearray()

    def append_audio(self, chunk: bytes) -> None:
        self._audio_buffer.extend(chunk)

    async def process_end_of_utterance(self) -> PipelineResult | None:
        audio_bytes = bytes(self._audio_buffer)
        self._audio_buffer.clear()

        if not audio_bytes:
            return None

        t0 = time.perf_counter()

        t1 = time.perf_counter()
        transcript = await transcribe(audio_bytes)
        stt_ms = (time.perf_counter() - t1) * 1000

        # Get session language for consistency
        session_data = await update_session(self.session_id, {"patient_phone": "guest"})
        session_language = session_data.get("language")
        
        # Detect language, preferring session language for consistency
        language = detect_language(transcript, session_language=session_language)

        t2 = time.perf_counter()
        agent_response, intent = await handle_message(
            session_id=self.session_id,
            user_text=transcript,
            language=language,
        )
        llm_ms = (time.perf_counter() - t2) * 1000

        t3 = time.perf_counter()
        audio_bytes_out = await synthesize(agent_response, language)
        tts_ms = (time.perf_counter() - t3) * 1000

        total_ms = (time.perf_counter() - t0) * 1000
        latency = LatencyBreakdown(
            stt_ms=round(stt_ms, 2),
            llm_ms=round(llm_ms, 2),
            tts_ms=round(tts_ms, 2),
            total_ms=round(total_ms, 2),
        )

        logger.info(
            "pipeline_latency",
            session_id=self.session_id,
            stt_ms=latency.stt_ms,
            llm_ms=latency.llm_ms,
            tts_ms=latency.tts_ms,
            total_ms=latency.total_ms,
        )

        audio_base64 = base64.b64encode(audio_bytes_out).decode("utf-8") if audio_bytes_out else ""

        return PipelineResult(
            transcript=transcript,
            language=language,
            agent_response=agent_response,
            intent=intent,
            audio_base64=audio_base64,
            latency=latency,
        )
