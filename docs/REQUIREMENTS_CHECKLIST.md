# 2Care Assignment – Requirements Checklist

Reference: assignment PDF (Real-Time Multilingual Voice AI Agent, Clinical Appointment Booking).

---

## 1. Objective

| Requirement | Status |
|-------------|--------|
| Real-time voice AI for clinical appointments | Done |
| Understand spoken language | Done (STT) |
| Convert speech to text | Done (Whisper) |
| AI interprets request | Done (LLM) |
| Book / reschedule / cancel appointments | Done |
| Speak responses back | Done (TTS) |
| Three languages: English, Hindi, Tamil | Done + auto detection |
| Contextual memory (conversation + past) | Done (session + persistent) |
| Outbound campaigns (reminders, follow-ups) | Done (scheduler; call initiation is stub) |
| Target latency < 450 ms | Done (measured and logged) |
| Latency measured and logged | Done (STT, LLM, TTS, total) |

---

## 2. Technical Requirements

| Technology | Status |
|------------|--------|
| Python (AI, agent) | Done |
| WebSockets | Done |
| FastAPI | Done |
| Redis | Done (+ in-memory fallback) |
| Whisper / Speech API | Done (OpenAI Whisper) |
| LLM (OpenAI) | Done |
| TTS | Done (OpenAI TTS) |
| PostgreSQL / store | Done (PostgreSQL models + SQLite option) |
| Docker | Done (Dockerfile + docker-compose) |

---

## 3. Required AI Components

| Component | Status |
|-----------|--------|
| Speech-to-Text | Done |
| Language Detection | Done |
| LLM Agent | Done |
| Tool Orchestration | Done |
| Text-to-Speech | Done |

---

## 4. Pipeline Architecture

| Step | Status |
|------|--------|
| User Speech → STT | Done |
| Language Detection | Done |
| AI Agent (LLM) | Done |
| Tool Orchestration | Done |
| Appointment Service | Done |
| Text Response → TTS | Done |
| Audio Response | Done |

---

## 5. Project Features

| Feature | Status |
|---------|--------|
| Appointment booking | Done |
| Rescheduling | Done |
| Cancellation | Done |
| Conflict detection | Done |
| Doctor availability | Done |
| Alternative slot suggestions | Done (in engine messages) |

---

## 6. Multilingual

| Item | Status |
|------|--------|
| English | Done |
| Hindi | Done |
| Tamil | Done |
| Auto language detection | Done |

---

## 7. Contextual Memory

| Type | Status |
|------|--------|
| Session memory (e.g. intent, doctor in turn) | Done (Redis / in-memory) |
| Persistent memory (preferred language, last doctor) | Done (Redis / in-memory) |

---

## 8. Outbound Campaign Mode

| Item | Status |
|------|--------|
| Scheduler for reminders / follow-ups | Done |
| Actual outbound call initiation | Stub (extend with Twilio etc.) |

---

## 9. Database Design

| Table / Rule | Status |
|--------------|--------|
| appointments (id, patient_id, doctor_id, date, time, status) | Done |
| doctor_schedule / availability | Done (slots + conflict check) |
| No double bookings | Done |
| No past times | Done |
| Valid doctor handling | Done |

---

## 10. Error Handling

| Scenario | Status |
|----------|--------|
| LLM failure → fallback “Could you repeat?” | Done |
| Scheduling conflict → alternative slots | Done |

---

## 11. Project Structure (per PDF)

| Folder | Status |
|--------|--------|
| backend (api, routes) | Done |
| agent (prompt, reasoning, tools) | Done |
| memory (session_memory, persistent_memory) | Done |
| services (speech_to_text, text_to_speech, language_detection) | Done |
| scheduler (appointment_engine, campaign_scheduler) | Done |
| docs | Done |

---

## 12. Submission Deliverables

| Item | Status |
|------|--------|
| Full project code | Done |
| Clear structure | Done |
| README: setup, architecture, memory, latency, trade-offs, limitations | Done |
| Architecture diagram | Done (docs/ARCHITECTURE.md; export to PNG/PDF if required) |
| Loom video | Your responsibility |

---

## 13. Bonus (Optional)

| Item | Status |
|------|--------|
| Interrupt / barge-in | Not done |
| Redis TTL | Done |
| Horizontal scaling | Not done |
| Cloud deployment | Not done |
| Background campaign scheduler | Done |

---

**Summary:** All mandatory PDF requirements are covered. Outbound “call initiation” is a stub; reminder/follow-up logic runs in the scheduler and can be wired to telephony when needed.
