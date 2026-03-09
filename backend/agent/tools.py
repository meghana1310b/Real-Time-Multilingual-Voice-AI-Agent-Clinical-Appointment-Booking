"""Tool implementations for appointment actions."""
from typing import Optional

from backend.scheduler.appointment_engine import (
    check_availability,
    book_appointment,
    cancel_appointment,
    reschedule_appointment,
)


def tool_check_availability(doctor_specialty: str, day_offset: int = 0) -> str:
    slots = check_availability(doctor_specialty, day_offset)
    if not slots:
        return f"No slots available for {doctor_specialty}."
    return f"Available slots: {', '.join(slots)}"


def tool_book_appointment(
    patient_phone: str,
    doctor_specialty: str,
    slot: str,
    day_offset: int = 0,
) -> str:
    result = book_appointment(patient_phone, doctor_specialty, slot, day_offset)
    return result


def tool_cancel_appointment(patient_phone: str, appointment_id: Optional[int] = None) -> str:
    result = cancel_appointment(patient_phone, appointment_id)
    return result


def tool_reschedule_appointment(
    patient_phone: str,
    appointment_id: Optional[int],
    new_slot: str,
    day_offset: int = 0,
) -> str:
    result = reschedule_appointment(patient_phone, appointment_id, new_slot, day_offset)
    return result
