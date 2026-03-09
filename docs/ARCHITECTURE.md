# 2Care Voice AI Agent – Architecture

## High-Level Flow

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ User Speech │────▶│ Speech-to-Text   │────▶│ Language Detect  │
│ (Mic)       │     │ (Whisper)        │     │ (en/hi/ta)       │
└─────────────┘     └──────────────────┘     └────────┬────────┘
                                                      │
                                                      ▼
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ Audio Out   │◀────│ Text-to-Speech   │◀────│ LLM Agent       │
│ (Speaker)   │     │ (OpenAI TTS)     │     │ (Reasoning +    │
└─────────────┘     └──────────────────┘     │  Tool Calls)    │
                                             └────────┬────────┘
                                                      │
                                                      ▼
                                             ┌─────────────────┐
                                             │ Tool Orchestr.  │
                                             │ → check_avail   │
                                             │ → book          │
                                             │ → cancel        │
                                             │ → reschedule    │
                                             └────────┬────────┘
                                                      │
                                                      ▼
                                             ┌─────────────────┐
                                             │ Appointment     │
                                             │ Engine + PG     │
                                             └─────────────────┘
```

## Components

| Component | Tech | Role |
|-----------|------|------|
| STT | OpenAI Whisper | Speech → text |
| Language Detection | langdetect | en / hi / ta |
| LLM Agent | OpenAI GPT | Intent + tool selection |
| Tools | Python | check_availability, book, cancel, reschedule |
| Session Memory | Redis | Conversation context, pending intent |
| Persistent Memory | Redis | Patient prefs, last doctor |
| Appointment Engine | PostgreSQL | Appointments, conflict handling |
| Campaign Scheduler | APScheduler | Reminders, follow-ups |

## Latency Target

&lt; 450 ms from speech end to first audio response.

Measured stages:

- STT
- LLM
- TTS
- Total

## Data Flow

1. WebSocket receives audio chunks.
2. Empty chunk signals end of utterance.
3. Pipeline: STT → language → agent (LLM + tools) → TTS.
4. JSON + base64 audio returned over WebSocket.
