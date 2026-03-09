# 2Care Voice AI Agent

Real-time multilingual voice AI agent for clinical appointment booking (English, Hindi, Tamil).

## Architecture

```
User Speech → STT (Whisper) → Language Detection → LLM Agent → Tool Orchestration
    → Appointment Engine → Text Response → TTS → Audio Response
```

- **Session memory** (Redis): conversation context, pending intent
- **Persistent memory** (Redis): patient preferences, last doctor, history
- **Target latency**: < 450 ms from speech end to first audio

## Setup (no Docker needed)

1. Copy env and set `OPENAI_API_KEY`:
   ```powershell
   copy .env.example .env
   ```
   Edit `.env` and add your OpenAI API key.

2. Install:
   ```powershell
   python -m pip install -r requirements.txt
   ```

3. Seed doctors:
   ```powershell
   python scripts/seed_doctors.py
   ```

4. Run:
   ```powershell
   python run.py
   ```
   Open http://localhost:8000 for the voice UI.

Defaults use **SQLite** (`voice_ai.db`) and **in-memory** session storage—no Docker or Redis required.

---

## Setup (with Docker)

```powershell
docker compose up -d
```
Then set in `.env`: `DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/voice_ai_appointments` and `REDIS_URL=redis://localhost:6379/0`.

## WebSocket API

Connect to `ws://localhost:8000/ws/voice`:

- Send binary audio chunks while speaking
- Send empty chunk to signal end-of-utterance
- Receive: `transcript`, `response`, `audio` (base64), `latency`

## Memory Design

| Layer      | Storage | TTL   | Content                          |
|------------|---------|-------|----------------------------------|
| Session    | Redis   | 1 hr  | messages, intent, doctor         |
| Persistent | Redis   | 1 yr  | preferred_language, last_doctor  |

## Latency Breakdown

Logged per request:

- `stt_ms`: Speech-to-text
- `llm_ms`: Agent reasoning + tools
- `tts_ms`: Text-to-speech
- `total_ms`: End-to-end

## Outbound Campaigns

Background scheduler runs:

- Appointment reminders (every 60 min)
- Follow-up checkups (daily)

Extend `backend/scheduler/campaign_scheduler.py` for production call initiation.

## Project Structure

```
2care/
├── backend/
│   ├── api/           # Routes, middleware
│   ├── agent/         # Prompt, reasoning, tools
│   ├── db/            # Models, database
│   ├── memory/        # Session + persistent
│   ├── scheduler/     # Appointment engine, campaigns
│   └── services/      # STT, TTS, language detection, pipeline
├── scripts/
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## Trade-offs

- Single LLM call (no tool loop) for lower latency
- Redis for memory; Postgres/SQLite for appointments
- Sync DB access; async for I/O-heavy services

## Known Limitations

- **Outbound campaigns**: Scheduler runs reminder/follow-up jobs but does not initiate real phone calls; add telephony (e.g. Twilio) for production.
- **Barge-in**: No interrupt handling; user must finish speaking before agent responds.
- **Architecture diagram**: See `docs/ARCHITECTURE.md`; export to PNG/PDF for submission if required.
