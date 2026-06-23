"""
create_users.py — DEVELOPMENT-ONLY initial user setup.

Passwords are read from environment variables. No hardcoded defaults.

Usage:
    ADMIN_PASSWORD=<pw> ENGINEER_PASSWORD=<pw> python create_users.py
"""
import os
import sys
sys.path.insert(0, '.')

from app.database import SessionLocal, User
from passlib.context import CryptContext
from datetime import datetime

ADMIN_PW = os.getenv("ADMIN_PASSWORD", "")
ENG_PW   = os.getenv("ENGINEER_PASSWORD", "")
if not ADMIN_PW or not ENG_PW:
    print("ERROR: Set ADMIN_PASSWORD and ENGINEER_PASSWORD environment variables before running.")
    sys.exit(1)

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
db = SessionLocal()

try:
    existing_count = db.query(User).count()
    print(f"Existing users: {existing_count}")

    if existing_count == 0:
        admin = User(
            username="admin",
            email="admin@example.com",
            full_name="System Administrator",
            hashed_password=pwd_context.hash(ADMIN_PW),
            disabled=False,
            created_at=datetime.utcnow()
        )
        engineer = User(
            username="engineer",
            email="engineer@example.com",
            full_name="Maintenance Engineer",
            hashed_password=pwd_context.hash(ENG_PW),
            disabled=False,
            created_at=datetime.utcnow()
        )
        db.add(admin)
        db.add(engineer)
        db.commit()
        print("[OK] Created admin and engineer users with passwords from environment variables.")
    else:
        print("[OK] Users already exist:")
        for user in db.query(User).all():
            print(f"  - {user.username} ({user.email})")

except Exception as e:
    print(f"Error: {e}")
    db.rollback()
finally:
    db.close()
