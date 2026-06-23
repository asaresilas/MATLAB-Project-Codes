"""
reset_passwords.py — DEVELOPMENT-ONLY password reset utility.

WARNING: This script must NEVER be run in a production environment.
Passwords are read exclusively from environment variables — no hardcoded
defaults exist in this script.

Usage (development only):
    ADMIN_PASSWORD=<new-pw> ENGINEER_PASSWORD=<new-pw> python reset_passwords.py
"""
import os
import sys
import logging
sys.path.insert(0, '.')

from app.database import SessionLocal, User
from passlib.context import CryptContext

ADMIN_PW = os.getenv("ADMIN_PASSWORD", "")
ENG_PW   = os.getenv("ENGINEER_PASSWORD", "")
if not ADMIN_PW or not ENG_PW:
    print("ERROR: Set ADMIN_PASSWORD and ENGINEER_PASSWORD environment variables before running.")
    print("       This script must NOT be run with empty or default passwords.")
    sys.exit(1)

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
db = SessionLocal()

try:
    admin = db.query(User).filter(User.username == 'admin').first()
    if admin:
        admin.hashed_password = pwd_context.hash(ADMIN_PW)
        logger.info("[OK] Admin password updated from ADMIN_PASSWORD env var.")
    else:
        logger.error("[ERROR] Admin user not found in database.")

    engineer = db.query(User).filter(User.username == 'engineer').first()
    if engineer:
        engineer.hashed_password = pwd_context.hash(ENG_PW)
        logger.info("[OK] Engineer password updated from ENGINEER_PASSWORD env var.")
    else:
        logger.error("[ERROR] Engineer user not found in database.")

    db.commit()
    logger.info("[OK] Password reset complete.")

except Exception as e:
    logger.error(f"[ERROR] {e}")
    db.rollback()
finally:
    db.close()
