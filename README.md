Real-Time Multilingual Voice AI Agent

A voice-based AI agent that can communicate with patients and manage clinical appointments automatically in English, Hindi, and Tamil.

---

## Objective
The system allows patients to:
- Book, reschedule, and cancel appointments
- Communicate in multiple languages
- Receive proactive reminders
- Maintain conversation context for smoother interactions

---

## Features
- Real-time voice interaction using WebSockets
- Speech-to-text (STT) and text-to-speech (TTS) conversion
- Multilingual support: English, Hindi, Tamil
- Contextual memory: session + persistent
- Appointment scheduling with conflict detection
- Outbound reminder campaigns

---

## Tech Stack
- **Backend:** FastAPI (Python)
- **Database:** PostgreSQL, Redis
- **AI Models:** Whisper/STT, OpenAI/LLaMA LLM, TTS engine
- **Communication:** WebSockets
- **Deployment:** Docker

---

## Project Structure

voice-ai-agent/
├── backend/
│ ├── api/
│ ├── controllers/
│ └── routes/
├── agent/
│ ├── prompt/
│ ├── reasoning/
│ └── tools/
├── memory/
│ ├── session_memory/
│ └── persistent_memory/
├── services/
│ ├── speech_to_text/
│ ├── text_to_speech/
│ └── language_detection/
├── scheduler/
│ └── appointment_engine/
└── docs/


---

## Setup Instructions

1. Clone the repository:
```bash
git clone <your-repo-url>
cd voice-ai-agent

Create a virtual environment and activate it:

python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

Install dependencies:

pip install -r requirements.txt

Run the backend server:

uvicorn backend.main:app --reload

Open frontend (if any) and connect to the backend WebSocket API.

System Architecture
User Speech → STT → Language Detection → AI Agent → Tool Orchestration → Appointment Service → TTS → Audio Response

STT: Converts voice to text

AI Agent: Understands intent and calls backend tools

Memory: Session and persistent user context

Tools: Appointment booking, rescheduling, and cancellations

Include docs/architecture-diagram.png in your repo for visual reference.

Memory Design

Session Memory: Tracks current conversation context

Persistent Memory: Stores user history (preferred language, past appointments)

Database Tables: appointments, doctor_schedule

Latency & Performance

Speech recognition: 120 ms

Agent reasoning: 200 ms

Speech synthesis: 100 ms

Total target latency: < 450 ms

Known Limitations

Currently supports only three languages

Outbound campaign limited to reminders

Requires internet connection for AI API calls

Future Improvements / Trade-offs

Interrupt handling (barge-in)

Horizontal scaling with multiple agents

Cloud deployment

Advanced AI reasoning with richer context

Testing

Book appointment → Should confirm slot

Cancel appointment → Should remove booking

Reschedule → Should suggest alternative slot if conflict

Language switching → Agent responds in selected language






