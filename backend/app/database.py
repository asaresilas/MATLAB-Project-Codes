"""
Database Integration for User Management

This module provides SQLite database integration for OAuth 2.0 user management.
Can be easily upgraded to PostgreSQL or MySQL for production.
"""

from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
import os
import logging

def _utcnow() -> datetime:
    """Return the current UTC time as a timezone-aware datetime.
    Used as the default for all timestamp columns so every DB record
    carries the exact date and time it was written, regardless of when
    the server is started or what the host clock is set to.
    """
    return datetime.now(timezone.utc)

# Set up logging
logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./users.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Models
class User(Base):
    """User model for database"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String)
    hashed_password = Column(String, nullable=False)
    disabled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)
    last_login = Column(DateTime, nullable=True)

class APIKey(Base):
    """API Key model for simple authentication"""
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    key_hash = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, nullable=False)
    description = Column(String)
    created_at = Column(DateTime, default=_utcnow)
    last_used = Column(DateTime, nullable=True)
    active = Column(Boolean, default=True)

class PredictionLog(Base):
    """Log of all predictions made"""
    __tablename__ = "prediction_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    endpoint = Column(String, nullable=False)
    model_used = Column(String, nullable=False)
    rul_prediction = Column(Integer, nullable=True)
    fault_detected = Column(String, nullable=True)
    timestamp = Column(DateTime, default=_utcnow)
    response_time_ms = Column(Integer, nullable=True)


class SensorReading(Base):
    """
    Sensor readings received from MATLAB/Simulink with their AI-predicted health state.

    Written concurrently with every prediction sent to MATLAB — the DB write
    never blocks the WebSocket response (runs in asyncio.to_thread).

    health_state is the definitive system label: NORMAL | WARNING | CRITICAL | UNKNOWN

    Physical sensor columns (directly queryable — no JSON parsing needed):
      rpm, torque_nm              : mechanical operating point
      temp_motor_c, temp_ambient_c: thermal readings
      vib_rms, vib_peak           : vibration magnitude (g)
      ia_rms, ib_rms, ic_rms      : 3-phase stator currents (A)
    """
    __tablename__ = "sensor_readings"

    id              = Column(Integer,  primary_key=True, index=True)
    timestamp       = Column(DateTime, default=_utcnow, index=True, nullable=False)
    client_id       = Column(String,   index=True,  nullable=False)
    machine_id      = Column(String,   nullable=True)

    # ── Physical sensor values (one column per measurement) ───────────────────
    # Mechanical
    rpm             = Column(Float,    nullable=True)   # rotor speed [RPM]
    torque_nm       = Column(Float,    nullable=True)   # shaft torque [Nm]

    # Thermal
    temp_motor_c    = Column(Float,    nullable=True)   # motor winding temperature [°C]
    temp_ambient_c  = Column(Float,    nullable=True)   # ambient temperature [°C]

    # Vibration (computed over 2048-sample window)
    vib_rms         = Column(Float,    nullable=True)   # vibration RMS magnitude [g]
    vib_peak        = Column(Float,    nullable=True)   # vibration peak magnitude [g]
    vib_samples     = Column(Integer,  nullable=True)   # number of samples in window

    # 3-Phase stator currents (RMS over window)
    ia_rms          = Column(Float,    nullable=True)   # Phase A current RMS [A]
    ib_rms          = Column(Float,    nullable=True)   # Phase B current RMS [A]
    ic_rms          = Column(Float,    nullable=True)   # Phase C current RMS [A]

    # Thermal camera
    has_thermal     = Column(Boolean,  nullable=True, default=False)  # thermal image present?

    # Full compact summary JSON (keeps extra detail without bloating columns)
    sensor_data_json = Column(Text,    nullable=True)

    # ── AI prediction outputs ─────────────────────────────────────────────────
    health_state    = Column(String,   nullable=False, default="UNKNOWN")  # NORMAL/WARNING/CRITICAL/UNKNOWN
    confidence      = Column(Float,    nullable=True)   # meta-fusion confidence [0–1]
    uncertainty     = Column(Float,    nullable=True)   # Shannon entropy uncertainty [0–1]
    rul_hours       = Column(Float,    nullable=True)   # Remaining Useful Life [hours]
    model_used      = Column(String,   nullable=True)   # which model pipeline answered
    inference_time_ms = Column(Float,  nullable=True)   # end-to-end inference latency [ms]


# Database initialization
def init_db():
    """
    Initialize database: create all tables, then apply any missing column
    migrations so new columns added to the ORM model are added to an
    existing DB file without requiring a full drop-and-recreate.
    """
    Base.metadata.create_all(bind=engine)
    logger.info("[OK] Database tables created/verified")
    _apply_migrations()


def _apply_migrations():
    """
    Lightweight forward-only migration: adds any columns that exist in the
    ORM model but are missing from the live database file.

    This replaces the need for Alembic in development / capstone deployments.
    Safe to call on every startup — it only issues ALTER TABLE when a column
    is genuinely absent, and never drops or modifies existing columns.
    """
    import sqlite3 as _sqlite3

    if "sqlite" not in DATABASE_URL:
        # PostgreSQL / MySQL already managed by create_all + proper Alembic
        return

    db_path = DATABASE_URL.replace("sqlite:///", "").lstrip("./")
    import os as _os
    db_path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", db_path)
    db_path = _os.path.normpath(db_path)

    if not _os.path.exists(db_path):
        return  # Brand-new DB — create_all already handled it

    con = _sqlite3.connect(db_path)
    cur = con.cursor()

    # Desired columns per table: (table_name, col_name, sql_type)
    desired = [
        # sensor_readings — physical sensor columns added in v2.2
        ("sensor_readings", "rpm",            "FLOAT"),
        ("sensor_readings", "torque_nm",       "FLOAT"),
        ("sensor_readings", "temp_motor_c",    "FLOAT"),
        ("sensor_readings", "temp_ambient_c",  "FLOAT"),
        ("sensor_readings", "vib_rms",         "FLOAT"),
        ("sensor_readings", "vib_peak",        "FLOAT"),
        ("sensor_readings", "vib_samples",     "INTEGER"),
        ("sensor_readings", "ia_rms",          "FLOAT"),
        ("sensor_readings", "ib_rms",          "FLOAT"),
        ("sensor_readings", "ic_rms",          "FLOAT"),
        ("sensor_readings", "has_thermal",     "BOOLEAN"),
    ]

    for table, col, col_type in desired:
        cur.execute(f"PRAGMA table_info([{table}])")
        existing_cols = {row[1] for row in cur.fetchall()}
        if col not in existing_cols:
            cur.execute(f"ALTER TABLE [{table}] ADD COLUMN {col} {col_type}")
            logger.info("[migration] Added column %s.%s (%s)", table, col, col_type)

    con.commit()
    con.close()

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Seed initial users
def seed_users():
    """
    Create initial admin and engineer users.

    Requires ADMIN_PASSWORD and ENGINEER_PASSWORD environment variables.
    Raises RuntimeError if either is unset to prevent accidental deployment
    without credentials.
    """
    from passlib.context import CryptContext

    admin_pw = os.getenv("ADMIN_PASSWORD", "")
    eng_pw   = os.getenv("ENGINEER_PASSWORD", "")
    if not admin_pw or not eng_pw:
        raise RuntimeError(
            "seed_users() requires ADMIN_PASSWORD and ENGINEER_PASSWORD "
            "environment variables. Set them before running."
        )

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    db = SessionLocal()

    try:
        if db.query(User).count() > 0:
            logger.info("Users already exist, skipping seed")
            return

        admin = User(
            username="admin",
            email="admin@example.com",
            full_name="System Administrator",
            hashed_password=pwd_context.hash(admin_pw[:72]),  # bcrypt 72-byte limit
            disabled=False
        )
        engineer = User(
            username="engineer",
            email="engineer@example.com",
            full_name="Maintenance Engineer",
            hashed_password=pwd_context.hash(eng_pw[:72]),
            disabled=False
        )
        db.add(admin)
        db.add(engineer)
        db.commit()
        logger.info("[OK] Initial users created from environment variables.")

    except Exception as e:
        logger.error(f"Error seeding users: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
    seed_users()
