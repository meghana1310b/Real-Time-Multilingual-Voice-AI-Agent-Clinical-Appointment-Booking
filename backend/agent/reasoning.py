"""LLM agent reasoning and tool orchestration."""
import json
import re
from typing import Optional

from openai import AsyncOpenAI

from backend.config import get_settings
from backend.agent.prompt import SYSTEM_PROMPT
from backend.agent.tools import (
    tool_check_availability,
    tool_book_appointment,
    tool_cancel_appointment,
    tool_reschedule_appointment,
)
from backend.memory.session_memory import get_session, update_session, append_message
from backend.memory.persistent_memory import get_patient, update_patient

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


def _parse_intent(text: str) -> str:
    m = re.search(r"INTENT:\s*(\w+)", text, re.I)
    return (m.group(1) or "general").lower()


def _extract_tool_call(response: str) -> Optional[dict]:
    # Try JSON format first: TOOL: {...}
    m = re.search(r"TOOL:\s*(\{[\s\S]*?\})", response)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            return None
    
    # Try function call format: FUNCTION_NAME(args)
    m = re.search(r"(CHECK_DOCTOR_AVAILABILITY|BOOK_APPOINTMENT|RESCHEDULE_APPOINTMENT|CANCEL_APPOINTMENT)\(([^)]*)\)", response)
    if not m:
        return None
    
    func_name = m.group(1).lower()
    args_str = m.group(2).strip()
    
    # Parse arguments - split by comma and clean quotes
    args_list = [arg.strip().strip('"\' ') for arg in args_str.split(',')]
    
    if func_name == "check_doctor_availability" and len(args_list) >= 2:
        return {
            "name": "check_availability",
            "args": {"doctor": args_list[0], "day_offset": 0}
        }
    elif func_name == "book_appointment" and len(args_list) >= 4:
        return {
            "name": "book_appointment",
            "args": {"doctor": args_list[1], "slot": args_list[3], "day_offset": 0}
        }
    elif func_name == "reschedule_appointment" and len(args_list) >= 3:
        return {
            "name": "reschedule_appointment",
            "args": {"appointment_id": args_list[0], "new_slot": args_list[2], "day_offset": 0}
        }
    elif func_name == "cancel_appointment" and len(args_list) >= 1:
        return {
            "name": "cancel_appointment",
            "args": {"appointment_id": args_list[0]}
        }
    
    return None


async def _execute_tool(name: str, args: dict, session_ctx: dict) -> str:
    ctx = session_ctx
    patient_id = ctx.get("patient_phone", "unknown")
    
    if name == "check_availability":
        return tool_check_availability(
            doctor_specialty=args.get("doctor", ctx.get("doctor", "general")),
            day_offset=args.get("day_offset", 0),
        )
    if name == "book_appointment":
        return tool_book_appointment(
            patient_phone=patient_id,
            doctor_specialty=args.get("doctor", ctx.get("doctor", "general")),
            slot=args.get("slot", ""),
            day_offset=args.get("day_offset", 0),
        )
    if name == "cancel_appointment":
        return tool_cancel_appointment(
            patient_phone=patient_id,
            appointment_id=args.get("appointment_id"),
        )
    if name == "reschedule_appointment":
        return tool_reschedule_appointment(
            patient_phone=patient_id,
            appointment_id=args.get("appointment_id"),
            new_slot=args.get("slot", ""),
            day_offset=args.get("day_offset", 0),
        )
    return "Unknown tool"


async def handle_message(
    session_id: str,
    user_text: str,
    language: str,
    patient_id: Optional[str] = None,
) -> tuple[str, str]:
    client = _get_client()
    session = await get_session(session_id)
    patient = await get_patient(patient_id or "unknown") if patient_id else {}
    
    preferred_lang = session.get("language") or patient.get("preferred_language", language)
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]
    
    for m in session.get("messages", [])[-10:]:
        messages.append({"role": m["role"], "content": m["content"]})
    
    # Build rich context note showing collected information
    collected_items = []
    missing_items = []
    
    # Track collected information
    if session.get("patient_name"):
        collected_items.append(f"Patient Name: {session['patient_name']}")
    else:
        missing_items.append("patient_name")
    
    if session.get("doctor"):
        collected_items.append(f"Doctor/Specialty: {session['doctor']}")
    else:
        missing_items.append("doctor_specialty")
    
    if session.get("preferred_date"):
        collected_items.append(f"Appointment Date: {session['preferred_date']}")
    else:
        missing_items.append("appointment_date")
        
    if session.get("preferred_time"):
        collected_items.append(f"Appointment Time: {session['preferred_time']}")
    else:
        missing_items.append("appointment_time")
        
    if session.get("visit_reason"):
        collected_items.append(f"Reason for Visit: {session['visit_reason']}")
    else:
        missing_items.append("reason_for_visit")
    
    if session.get("appointment_status"):
        collected_items.append(f"Appointment Status: {session['appointment_status']}")
    
    # Build context string
    context_note = f"Session Language: {preferred_lang}. "
    
    if collected_items:
        context_note += f"COLLECTED INFORMATION: {' | '.join(collected_items)}. "
    
    if missing_items:
        context_note += f"STILL NEED: {', '.join(missing_items)}. "
    
    if session.get("intent"):
        context_note += f"Current Intent: {session['intent']}. "
    
    if patient.get("last_doctor"):
        context_note += f"Patient's Previous Doctor: {patient['last_doctor']}. "
    
    if session.get("messages"):
        context_note += f"Message Count: {len(session.get('messages', []))}. "
    
    # Build user message with context
    user_msg = user_text
    if context_note:
        user_msg = f"[Context: {context_note}]\nUser: {user_text}"
    
    messages.append({"role": "user", "content": user_msg})

    try:
        response = await client.chat.completions.create(
            model=_settings.LLM_MODEL,
            messages=messages,
            max_tokens=256,
            temperature=0.3,
        )
    except Exception:
        return (
            "I'm having trouble processing that request. Could you repeat?",
            "general",
        )

    content = response.choices[0].message.content or ""
    intent = _parse_intent(content)
    text_response = re.sub(r"\nINTENT:.*", "", content, flags=re.I).strip()
    
    tool = _extract_tool_call(content)
    if tool:
        result = await _execute_tool(tool.get("name", ""), tool.get("args", {}), session)
        text_response = result
    
    await append_message(session_id, "user", user_text)
    await append_message(session_id, "assistant", text_response)
    
    # Extract information from user text for session tracking
    extracted_info = _extract_patient_info(user_text, language)
    
    # Update session with new information and ensure language consistency
    session_update = {
        "intent": intent,
        "language": preferred_lang,  # Always maintain session language
    }
    
    # Preserve doctor if not newly detected
    if session.get("doctor"):
        session_update["doctor"] = session.get("doctor")
    elif extracted_info.get("doctor"):
        session_update["doctor"] = extracted_info["doctor"]
    else:
        session_update["doctor"] = _guess_doctor(user_text)
    
    # Update collected information and preserve existing values
    if extracted_info.get("patient_name"):
        session_update["patient_name"] = extracted_info["patient_name"]
    elif session.get("patient_name"):
        session_update["patient_name"] = session.get("patient_name")
    
    if extracted_info.get("appointment_status"):
        session_update["appointment_status"] = extracted_info["appointment_status"]
    elif session.get("appointment_status"):
        session_update["appointment_status"] = session.get("appointment_status")
    
    if extracted_info.get("visit_reason"):
        session_update["visit_reason"] = extracted_info["visit_reason"]
    elif session.get("visit_reason"):
        session_update["visit_reason"] = session.get("visit_reason")
    
    if extracted_info.get("date"):
        session_update["preferred_date"] = extracted_info["date"]
    elif session.get("preferred_date"):
        session_update["preferred_date"] = session.get("preferred_date")
    
    if extracted_info.get("time"):
        session_update["preferred_time"] = extracted_info["time"]
    elif session.get("preferred_time"):
        session_update["preferred_time"] = session.get("preferred_time")
    
    await update_session(session_id, session_update)
    
    if patient_id:
        await update_patient(patient_id, {"preferred_language": language})
    
    return text_response, intent


def _extract_patient_info(text: str, language: str) -> dict:
    """Extract patient information from text (name, date, time patterns, intent, etc)."""
    info = {}
    text_lower = text.lower()
    
    # Detect appointment status/intent from keywords
    if any(word in text_lower for word in ["reschedule", "change", "move", "postpone", "delay"]):
        info["appointment_status"] = "reschedule"
    elif any(word in text_lower for word in ["cancel", "remove", "delete"]):
        info["appointment_status"] = "cancel"
    elif any(word in text_lower for word in ["book", "appointment", "schedule", "meet", "see"]):
        info["appointment_status"] = "new"
    elif any(word in text_lower for word in ["available", "slots", "times", "dates", "check"]):
        info["appointment_status"] = "check_availability"
    
    # Try to detect doctor specialty mentions
    specialties = {
        "cardiologist": "Cardiologist",
        "dermatologist": "Dermatologist",
        "orthopedic": "Orthopedic",
        "orthopedist": "Orthopedic",
        "general": "General Practitioner",
        "gp": "General Practitioner",
        "physician": "General Practitioner",
    }
    
    for spec_key, spec_value in specialties.items():
        if spec_key in text_lower:
            info["doctor"] = spec_value
            break
    
    # Look for common date patterns
    date_patterns = [
        r'\b(\d{1,2}[-/]\d{1,2})\b',  # dd/mm or dd-mm
        r'\b(tomorrow|today|next week|next monday|next tuesday|next wednesday|next thursday|next friday|next saturday|next sunday)\b'
    ]
    
    for pattern in date_patterns:
        m = re.search(pattern, text_lower)
        if m:
            info["date"] = m.group(1)
            break
    
    # Look for time patterns
    time_patterns = [
        r'\b(\d{1,2}:\d{2}\s*(?:am|pm|a\.m\.|p\.m\.))\b',
        r'\b(\d{1,2}\s*(?:am|pm|a\.m\.|p\.m\.))\b',
        r'\b(morning|afternoon|evening)\b'
    ]
    
    for pattern in time_patterns:
        m = re.search(pattern, text_lower)
        if m:
            info["time"] = m.group(1)
            break
    
    # Try to detect patient name (words after "my name is", "I'm", "I am", "call me", etc.)
    name_patterns = [
        r"(?:my name is|i'm|i am|call me|you can call me)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)",
        r"(?:this is|name is)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)",
    ]
    
    for pattern in name_patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            info["patient_name"] = m.group(1)
            break
    
    # Try to extract visit reason (after keywords like "because", "due to", "for", "I have", "I'm suffering from")
    reason_patterns = [
        r"(?:because|due to|reason|for|regarding|about)\s+([a-zA-Z\s]+?)(?:\.|,|$)",
        r"(?:I'm suffering from|I have|suffering from|have)\s+([a-zA-Z\s]+?)(?:\.|,|and|$)",
    ]
    
    for pattern in reason_patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            reason = m.group(1).strip()
            if reason and len(reason) > 2 and len(reason) < 100:
                info["visit_reason"] = reason
                break
    
    return info


def _guess_doctor(text: str) -> Optional[str]:
    text_lower = text.lower()
    for spec in ["cardiologist", "dermatologist", "general", "orthopedic"]:
        if spec in text_lower:
            return spec
    return None
