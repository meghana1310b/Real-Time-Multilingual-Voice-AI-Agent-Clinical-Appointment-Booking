"""Doctors and appointments API."""
from datetime import date, time
from typing import Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

from backend.db.database import SessionLocal
from backend.db.models import Doctor, Appointment, Patient

router = APIRouter()


class DoctorOut(BaseModel):
    id: int
    name: str
    specialty: str
    email: Optional[str]

    class Config:
        from_attributes = True


class AppointmentOut(BaseModel):
    id: int
    patient_phone: str
    doctor_name: str
    doctor_specialty: str
    date: str
    time_slot: str
    status: str

    class Config:
        from_attributes = True


@router.get("/api/doctors", response_model=list[DoctorOut])
def list_doctors(
    specialty: Optional[str] = Query(None, description="Filter by specialty"),
):
    db = SessionLocal()
    try:
        q = db.query(Doctor)
        if specialty:
            q = q.filter(Doctor.specialty.ilike(f"%{specialty}%"))
        doctors = q.all()
        return [DoctorOut(id=d.id, name=d.name, specialty=d.specialty, email=d.email) for d in doctors]
    finally:
        db.close()


@router.get("/api/appointments", response_model=list[AppointmentOut])
def list_appointments(
    status: Optional[str] = Query(None, description="scheduled, cancelled, completed"),
    limit: int = Query(50, le=200),
):
    db = SessionLocal()
    try:
        q = (
            db.query(Appointment)
            .join(Doctor, Appointment.doctor_id == Doctor.id)
            .join(Patient, Appointment.patient_id == Patient.id)
        )
        if status:
            q = q.filter(Appointment.status == status)
        rows = q.order_by(Appointment.date.desc(), Appointment.time_slot.desc()).limit(limit).all()
        return [
            AppointmentOut(
                id=a.id,
                patient_phone=a.patient.phone,
                doctor_name=a.doctor.name,
                doctor_specialty=a.doctor.specialty,
                date=a.date.isoformat(),
                time_slot=a.time_slot.strftime("%I:%M %p") if a.time_slot else "",
                status=a.status,
            )
            for a in rows
        ]
    finally:
        db.close()
