"""Seed doctors for appointment booking."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.db.database import SessionLocal, init_db
from backend.db.models import Doctor

DOCTORS = [
    {"name": "Dr Sharma", "specialty": "cardiologist", "email": "sharma@2care.ai"},
    {"name": "Dr Patel", "specialty": "dermatologist", "email": "patel@2care.ai"},
    {"name": "Dr Kumar", "specialty": "general", "email": "kumar@2care.ai"},
    {"name": "Dr Iyer", "specialty": "orthopedic", "email": "iyer@2care.ai"},
]


def main():
    init_db()
    db = SessionLocal()
    try:
        for d in DOCTORS:
            existing = db.query(Doctor).filter(Doctor.email == d["email"]).first()
            if not existing:
                db.add(Doctor(**d))
                print(f"Added {d['name']} ({d['specialty']})")
        db.commit()
    finally:
        db.close()
    print("Seed complete.")


if __name__ == "__main__":
    main()
