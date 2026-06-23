"""
MotorGuard Database Viewer
==========================
Run this any time — before, during, or after a simulation — to inspect
every record stored in the database.

Usage (from the backend/ folder):
    python view_database.py                        # full summary of all tables
    python view_database.py sensor                 # last 20 sensor readings
    python view_database.py sensor --all           # every sensor reading
    python view_database.py sensor --state CRITICAL  # filter by health state
    python view_database.py sensor --today         # only today's records
    python view_database.py sensor --export        # export to CSV file
    python view_database.py users                  # list user accounts
    python view_database.py logs                   # prediction log entries
"""

import sys
import os
import sqlite3
import json
from datetime import datetime, timezone

# ── Resolve DB path ───────────────────────────────────────────────────────────
_here   = os.path.dirname(os.path.abspath(__file__))
_db_env = os.getenv("DATABASE_URL", "")
if _db_env.startswith("sqlite:///"):
    DB_PATH = os.path.join(_here, _db_env.replace("sqlite:///", "").lstrip("./"))
else:
    DB_PATH = os.path.join(_here, "users.db")


def _conn():
    if not os.path.exists(DB_PATH):
        print(f"\n[ERROR] Database not found at:\n  {DB_PATH}")
        print("Start the backend server at least once so init_db() creates it.\n")
        sys.exit(1)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def _fmt_ts(ts_str):
    """Format a stored UTC timestamp to a readable string."""
    if not ts_str:
        return "-"
    for fmt in (
        "%Y-%m-%d %H:%M:%S.%f+00:00",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S.%f+00:00",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
    ):
        try:
            dt = datetime.strptime(str(ts_str)[:len(fmt)], fmt).replace(tzinfo=timezone.utc)
            return dt.strftime("%Y-%m-%d  %H:%M:%S  UTC")
        except ValueError:
            continue
    return str(ts_str)


# ── SUMMARY ──────────────────────────────────────────────────────────────────
def show_summary():
    con = _conn()
    cur = con.cursor()

    print()
    print("=" * 68)
    print("  MotorGuard - Database Summary")
    print(f"  File : {DB_PATH}")
    print(f"  Viewed: {datetime.now(timezone.utc).strftime('%Y-%m-%d  %H:%M:%S  UTC')}")
    print("=" * 68)

    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [r[0] for r in cur.fetchall()]

    for table in tables:
        cur.execute(f"SELECT COUNT(*) FROM [{table}]")
        count = cur.fetchone()[0]
        try:
            cur.execute(f"SELECT MIN(timestamp), MAX(timestamp) FROM [{table}]")
            row = cur.fetchone()
            ts_range = (f"  {_fmt_ts(row[0])}  ->  {_fmt_ts(row[1])}"
                        if row[0] else "  (no records yet)")
        except Exception:
            ts_range = ""
        print(f"\n  Table : {table}  ({count} rows)")
        if ts_range:
            print(f"  Range : {ts_range}")
        cur.execute(f"PRAGMA table_info([{table}])")
        cols = [r[1] for r in cur.fetchall()]
        print(f"  Cols  : {', '.join(cols)}")

    # Health state breakdown
    if "sensor_readings" in tables:
        print()
        print("  -- Health state breakdown (sensor_readings) --")
        cur.execute("""
            SELECT health_state, COUNT(*) AS cnt
            FROM sensor_readings
            GROUP BY health_state
            ORDER BY cnt DESC
        """)
        for row in cur.fetchall():
            bar = "#" * min(40, row["cnt"])
            print(f"    {row['health_state']:<10}  {row['cnt']:>5}  {bar}")

    con.close()
    print()
    print("  Commands:")
    print("    python view_database.py sensor            # last 20 readings")
    print("    python view_database.py sensor --today    # today only")
    print("    python view_database.py sensor --state CRITICAL")
    print("    python view_database.py sensor --export   # save CSV")
    print("    python view_database.py users")
    print()


# ── SENSOR READINGS ───────────────────────────────────────────────────────────
def show_sensor_readings(args):
    show_all     = "--all"    in args
    today_only   = "--today"  in args
    export_csv   = "--export" in args
    state_filter = None
    if "--state" in args:
        idx = args.index("--state")
        if idx + 1 < len(args):
            state_filter = args[idx + 1].upper()

    con  = _conn()
    cur  = con.cursor()

    where_clauses, params = [], []
    if today_only:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        where_clauses.append("timestamp LIKE ?")
        params.append(f"{today}%")
    if state_filter:
        where_clauses.append("health_state = ?")
        params.append(state_filter)

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
    limit_sql = "" if show_all else "LIMIT 20"

    cur.execute(f"""
        SELECT id, timestamp, client_id, machine_id,
               rpm, torque_nm, temp_motor_c, temp_ambient_c,
               vib_rms, vib_peak, vib_samples,
               ia_rms, ib_rms, ic_rms, has_thermal,
               health_state, confidence, uncertainty, rul_hours,
               model_used, inference_time_ms, sensor_data_json
        FROM sensor_readings
        {where_sql}
        ORDER BY id DESC
        {limit_sql}
    """, params)
    rows = cur.fetchall()

    cur.execute(f"SELECT COUNT(*) FROM sensor_readings {where_sql}", params)
    total = cur.fetchone()[0]
    con.close()

    if not rows:
        print("\n  No sensor readings found (check filters).\n")
        return

    # ── CSV export ────────────────────────────────────────────────────────────
    if export_csv:
        import csv as _csv
        fname = f"sensor_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        csv_path = os.path.join(_here, fname)
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            w = _csv.writer(f)
            w.writerow([
                "id", "timestamp_utc", "client_id", "machine_id",
                "rpm", "torque_nm", "temp_motor_c", "temp_ambient_c",
                "vib_rms", "vib_peak", "vib_samples",
                "ia_rms_A", "ib_rms_A", "ic_rms_A", "has_thermal",
                "health_state", "confidence_%", "uncertainty_%",
                "rul_hours", "model_used", "inference_time_ms",
            ])
            for r in rows:
                def _csv_f(v, d=4):
                    return f"{float(v):.{d}f}" if v is not None else ""
                w.writerow([
                    r["id"],
                    _fmt_ts(r["timestamp"]),
                    r["client_id"] or "",
                    r["machine_id"] or "",
                    _csv_f(r["rpm"], 1),
                    _csv_f(r["torque_nm"], 2),
                    _csv_f(r["temp_motor_c"], 1),
                    _csv_f(r["temp_ambient_c"], 1),
                    _csv_f(r["vib_rms"], 6),
                    _csv_f(r["vib_peak"], 6),
                    r["vib_samples"] or "",
                    _csv_f(r["ia_rms"], 4),
                    _csv_f(r["ib_rms"], 4),
                    _csv_f(r["ic_rms"], 4),
                    "Yes" if r["has_thermal"] else "No",
                    r["health_state"],
                    f"{r['confidence']*100:.2f}" if r["confidence"] is not None else "",
                    f"{r['uncertainty']*100:.2f}" if r["uncertainty"] is not None else "",
                    _csv_f(r["rul_hours"], 2),
                    r["model_used"] or "",
                    _csv_f(r["inference_time_ms"], 1),
                ])
        print(f"\n  [OK] Exported {len(rows)} rows  ->  {csv_path}\n")
        return

    # ── Pretty-print ──────────────────────────────────────────────────────────
    label = "all" if show_all else f"latest {min(20, total)}"
    print()
    print(f"  sensor_readings  --  {label} of {total} total records")
    if state_filter: print(f"  Filter : health_state = {state_filter}")
    if today_only:   print(f"  Filter : today only")
    print()

    HDR = (f"  {'ID':>5}  {'Date & Time (UTC)':<22}  {'State':<10}  "
           f"{'RPM':>6}  {'Torque':>7}  {'T-Mot':>6}  {'T-Amb':>6}  "
           f"{'Vib-RMS':>8}  {'Ia-RMS':>7}  {'RUL(h)':>7}  {'Conf':>6}  {'ms':>6}")
    print(HDR)
    print("  " + "-" * (len(HDR) - 2))

    STATE_ICON = {"NORMAL": "[OK]", "WARNING": "[WN]", "CRITICAL": "[CR]", "UNKNOWN": "[??]"}

    def _f(val, fmt=".1f", unit="", none="-"):
        """Format a float value or return dash if None."""
        if val is None:
            return none
        try:
            return f"{float(val):{fmt}}{unit}"
        except Exception:
            return none

    for r in rows:
        ts   = _fmt_ts(r["timestamp"])[:22]
        icon = STATE_ICON.get(r["health_state"], "[??]")
        state_str = f"{icon}{r['health_state']:<8}"

        # Sensor columns
        rpm     = _f(r["rpm"],           ".0f")
        torque  = _f(r["torque_nm"],     ".1f", " Nm")
        t_mot   = _f(r["temp_motor_c"],  ".1f", "C")
        t_amb   = _f(r["temp_ambient_c"],".1f", "C")
        vib     = _f(r["vib_rms"],       ".4f")
        ia      = _f(r["ia_rms"],        ".3f")
        rul     = _f(r["rul_hours"],     ".0f")
        conf    = _f(r["confidence"],    ".1%") if r["confidence"] is not None else "-"
        lat     = _f(r["inference_time_ms"], ".0f")

        print(f"  {r['id']:>5}  {ts:<22}  {state_str:<14}  "
              f"{rpm:>6}  {torque:>9}  {t_mot:>7}  {t_amb:>7}  "
              f"{vib:>8}  {ia:>7}  {rul:>7}  {conf:>6}  {lat:>6}")

    print()
    if total > len(rows):
        print(f"  (Showing {len(rows)} of {total} rows — use --all to see everything)\n")


# ── USERS ─────────────────────────────────────────────────────────────────────
def show_users():
    con  = _conn()
    rows = con.execute(
        "SELECT id, username, email, full_name, disabled, created_at FROM users"
    ).fetchall()
    con.close()

    print()
    print("  Users")
    print()
    print(f"  {'ID':>3}  {'Username':<16}  {'Full Name':<24}  {'Email':<28}  {'Status':<8}  {'Created'}")
    print("  " + "-" * 96)
    for r in rows:
        status = "disabled" if r["disabled"] else "active"
        print(f"  {r['id']:>3}  {r['username']:<16}  {(r['full_name'] or ''):<24}  "
              f"{r['email']:<28}  {status:<8}  {_fmt_ts(r['created_at'])}")
    print()


# ── PREDICTION LOG ────────────────────────────────────────────────────────────
def show_logs():
    con  = _conn()
    rows = con.execute(
        "SELECT id, timestamp, endpoint, model_used, rul_prediction, "
        "fault_detected, response_time_ms FROM prediction_logs ORDER BY id DESC LIMIT 30"
    ).fetchall()
    con.close()

    print()
    print("  Prediction Logs (latest 30)")
    print()
    if not rows:
        print("  No prediction log entries yet.\n")
        return
    print(f"  {'ID':>5}  {'Date & Time (UTC)':<24}  {'Endpoint':<24}  {'RUL':>5}  Fault")
    print("  " + "-" * 80)
    for r in rows:
        print(f"  {r['id']:>5}  {_fmt_ts(r['timestamp']):<24}  "
              f"{r['endpoint']:<24}  {str(r['rul_prediction'] or '—'):>5}  "
              f"{r['fault_detected'] or '—'}")
    print()


# ── ENTRY POINT ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    args = sys.argv[1:]
    cmd  = args[0].lower() if args else "summary"

    if cmd in ("sensor", "sensors", "readings", "data"):
        show_sensor_readings(args[1:])
    elif cmd in ("user", "users", "accounts"):
        show_users()
    elif cmd in ("log", "logs", "prediction", "predictions"):
        show_logs()
    else:
        show_summary()
