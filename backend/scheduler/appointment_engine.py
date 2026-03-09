"""Appointment scheduling engine with conflict detection and availability."""
from datetime import datetime, date, time, timedelta
from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from backend.db.database import SessionLocal
from backend.db.models import Doctor, Patient, Appointment, DoctorSchedule, AppointmentStatus


def _get_db() -> Session:
    return SessionLocal()


def _target_date(day_offset: int) -> date:
    return (datetime.utcnow() + timedelta(days=day_offset)).date()


def _parse_slot(slot_str: str) -> time:
    slot_str = slot_str.strip().upper().replace(".", ":")
    for fmt in ("%I:%M %p", "%H:%M", "%I%M%p"):
        try:
            dt = datetime.strptime(slot_str, fmt)
            return dt.time()
        except ValueError:
            continue
    return time(10, 0)


def _ensure_patient(phone: str) -> int:
    db = _get_db()
    try:
        p = db.query(Patient).filter(Patient.phone == phone).first()
        if p:
            return p.id
        pat = Patient(phone=phone)
        db.add(pat)
        db.commit()
        db.refresh(pat)
        return pat.id
    finally:
        db.close()


def _get_doctor_by_specialty(specialty: str) -> Optional[Doctor]:
    db = _get_db()
    try:
        spec = specialty.lower().strip()
        return db.query(Doctor).filter(Doctor.specialty.ilike(f"%{spec}%")).first()
    finally:
        db.close()


def _get_booked_slots(doctor_id: int, target_date: date) -> set:
    db = _get_db()
    try:
        rows = db.query(Appointment.time_slot).filter(
            and_(
                Appointment.doctor_id == doctor_id,
                Appointment.date == target_date,
                Appointment.status == AppointmentStatus.SCHEDULED.value,
            )
        ).all()
        return {r[0] for r in rows}
    finally:
        db.close()


DEFAULT_SLOTS = [
    time(9, 0), time(10, 0), time(11, 0), time(14, 0), time(15, 0), time(16, 0),
]


def check_availability(doctor_specialty: str, day_offset: int = 0) -> list[str]:
    doctor = _get_doctor_by_specialty(doctor_specialty)
    if not doctor:
        return []
    
    target = _target_date(day_offset)
    booked = _get_booked_slots(doctor.id, target)
    available = [t for t in DEFAULT_SLOTS if t not in booked]
    return [t.strftime("%I:%M %p") for t in available]


def book_appointment(
    patient_phone: str,
    doctor_specialty: str,
    slot: str,
    day_offset: int = 0,
) -> str:
    doctor = _get_doctor_by_specialty(doctor_specialty)
    if not doctor:
        return f"No doctor found for {doctor_specialty}."
    
    target = _target_date(day_offset)
    if target < datetime.utcnow().date():
        return "Cannot book in the past."
    
    time_slot = _parse_slot(slot)
    booked = _get_booked_slots(doctor.id, target)
    if time_slot in booked:
        slots = check_availability(doctor_specialty, day_offset)
        return f"That slot is taken. Available: {', '.join(slots)}."
    
    db = _get_db()
    try:
        patient_id = _ensure_patient(patient_phone)
        apt = Appointment(
            patient_id=patient_id,
            doctor_id=doctor.id,
            date=target,
            time_slot=time_slot,
            status=AppointmentStatus.SCHEDULED.value,
        )
        db.add(apt)
        db.commit()
        return f"Appointment with Dr {doctor.name} on {target} at {time_slot.strftime('%I:%M %p')} confirmed."
    except Exception as e:
        db.rollback()
        return f"Booking failed: {e}"
    finally:
        db.close()


def cancel_appointment(patient_phone: str, appointment_id: Optional[int] = None) -> str:
    db = _get_db()
    try:
        patient_id = _ensure_patient(patient_phone)
        q = db.query(Appointment).filter(
            Appointment.patient_id == patient_id,
            Appointment.status == AppointmentStatus.SCHEDULED.value,
        )
        if appointment_id:
            q = q.filter(Appointment.id == appointment_id)
        apt = q.first()
        if not apt:
            return "No upcoming appointment found to cancel."
        apt.status = AppointmentStatus.CANCELLED.value
        db.commit()
        return "Appointment cancelled."
    except Exception as e:
        db.rollback()
        return f"Cancellation failed: {e}"
    finally:
        db.close()


def reschedule_appointment(
    patient_phone: str,
    appointment_id: Optional[int],
    new_slot: str,
    day_offset: int = 0,
) -> str:
    db = _get_db()
    try:
        patient_id = _ensure_patient(patient_phone)
        q = db.query(Appointment).filter(
            Appointment.patient_id == patient_id,
            Appointment.status == AppointmentStatus.SCHEDULED.value,
        )
        if appointment_id:
            q = q.filter(Appointment.id == appointment_id)
        apt = q.first()
        if not apt:
            return "No upcoming appointment found to reschedule."
        
        target = _target_date(day_offset)
        time_slot = _parse_slot(new_slot)
        booked = _get_booked_slots(apt.doctor_id, target)
        if time_slot in booked:
            return "That slot is already booked. Please choose another."
        
        apt.date = target
        apt.time_slot = time_slot
        db.commit()
        return f"Appointment rescheduled to {target} at {time_slot.strftime('%I:%M %p')}."
    except Exception as e:
        db.rollback()
        return f"Reschedule failed: {e}"
    finally:
        db.close()
