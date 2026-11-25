import sqlite3
from typing import Dict, Any, List, Optional
import sys
from pathlib import Path

# Add parent directory to sys.path so config can be imported directly
CURRENT_DIR = Path(__file__).resolve().parent
PARENT_DIR = CURRENT_DIR.parent
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

import config

def get_connection() -> sqlite3.Connection:
    """Get a database connection with Row row_factory for dict-like access."""
    conn = sqlite3.connect(str(config.DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create the tables if they do not exist and seed default settings."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Sensor readings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sensor_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts INTEGER NOT NULL,
            motion INTEGER NOT NULL,
            lux REAL NOT NULL,
            distance_cm REAL NOT NULL,
            light TEXT NOT NULL,
            fan TEXT NOT NULL,
            mode TEXT NOT NULL
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sensor_readings_ts ON sensor_readings(ts)")

    # 2. Device events table (source: auto | dashboard | telegram)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS device_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts INTEGER NOT NULL,
            device TEXT NOT NULL,
            state TEXT NOT NULL,
            source TEXT NOT NULL
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_device_events_ts ON device_events(ts)")

    # 3. Alerts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts INTEGER NOT NULL,
            type TEXT NOT NULL,
            severity TEXT NOT NULL,
            acknowledged INTEGER DEFAULT 0
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_ts ON alerts(ts)")

    # 4. Energy log table (daily aggregated usage)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS energy_log (
            date TEXT NOT NULL,
            device TEXT NOT NULL,
            on_minutes REAL DEFAULT 0.0,
            kwh REAL DEFAULT 0.0,
            PRIMARY KEY (date, device)
        )
    """)

    # 5. Settings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    # Seed default settings if not existing
    default_settings = {
        "timeout_sec": str(config.DEFAULT_TIMEOUT_SEC),
        "lux_threshold": str(config.DEFAULT_LUX_THRESHOLD),
        "light_watts": str(config.DEFAULT_LIGHT_WATTS),
        "fan_watts": str(config.DEFAULT_FAN_WATTS),
        "tariff_per_kwh": str(config.DEFAULT_TARIFF_PER_KWH),
        "intrusion_distance_threshold": str(config.DEFAULT_INTRUSION_DISTANCE_THRESHOLD)
    }

    for k, v in default_settings.items():
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))

    conn.commit()
    conn.close()

# --- Sensor Readings Helpers ---

def insert_sensor_reading(ts: int, motion: bool, lux: float, distance_cm: float, light: str, fan: str, mode: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO sensor_readings (ts, motion, lux, distance_cm, light, fan, mode)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (ts, 1 if motion else 0, lux, distance_cm, light, fan, mode))
    inserted_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return inserted_id

def get_latest_sensor_reading() -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sensor_readings ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_recent_sensor_readings(limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sensor_readings ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in reversed(rows)]

# --- Device Events Helpers ---

def insert_device_event(ts: int, device: str, state: str, source: str = "auto") -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO device_events (ts, device, state, source)
        VALUES (?, ?, ?, ?)
    """, (ts, device, state, source))
    event_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return event_id

def get_recent_device_events(limit: int = 20) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM device_events ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# --- Alerts Helpers ---

def insert_alert(ts: int, alert_type: str, severity: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO alerts (ts, type, severity, acknowledged)
        VALUES (?, ?, ?, 0)
    """, (ts, alert_type, severity))
    alert_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return alert_id

def get_alerts(limit: int = 50, acknowledged: Optional[bool] = None) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    if acknowledged is None:
        cursor.execute("SELECT * FROM alerts ORDER BY id DESC LIMIT ?", (limit,))
    else:
        cursor.execute("SELECT * FROM alerts WHERE acknowledged = ? ORDER BY id DESC LIMIT ?", (1 if acknowledged else 0, limit))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_unacknowledged_alerts_count() -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM alerts WHERE acknowledged = 0")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def acknowledge_alert(alert_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE alerts SET acknowledged = 1 WHERE id = ?", (alert_id,))
    affected = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return affected

def acknowledge_all_alerts() -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE alerts SET acknowledged = 1 WHERE acknowledged = 0")
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected

# --- Energy Log Helpers ---

def update_energy_log(date_str: str, device: str, on_minutes_delta: float, kwh_delta: float):
    """
    Increment on_minutes and kwh for a specific date and device.
    Uses UPSERT (INSERT ... ON CONFLICT DO UPDATE).
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO energy_log (date, device, on_minutes, kwh)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(date, device) DO UPDATE SET
            on_minutes = on_minutes + excluded.on_minutes,
            kwh = kwh + excluded.kwh
    """, (date_str, device, on_minutes_delta, kwh_delta))
    conn.commit()
    conn.close()

def get_energy_history(days: int = 7) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT date, device, on_minutes, kwh 
        FROM energy_log 
        ORDER BY date DESC, device ASC
        LIMIT ?
    """, (days * 2,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in reversed(rows)]

def get_total_energy_today(date_str: str) -> Dict[str, float]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            COALESCE(SUM(on_minutes), 0.0) as total_minutes,
            COALESCE(SUM(kwh), 0.0) as total_kwh
        FROM energy_log
        WHERE date = ?
    """, (date_str,))
    row = cursor.fetchone()
    conn.close()
    return {"total_minutes": float(row["total_minutes"]), "total_kwh": float(row["total_kwh"])} if row else {"total_minutes": 0.0, "total_kwh": 0.0}

# --- Settings Helpers ---

def get_settings() -> Dict[str, str]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM settings")
    rows = cursor.fetchall()
    conn.close()
    return {r["key"]: r["value"] for r in rows}

def get_setting_float(key: str, default: float) -> float:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    if row:
        try:
            return float(row["value"])
        except ValueError:
            return default
    return default

def get_setting_int(key: str, default: int) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    if row:
        try:
            return int(row["value"])
        except ValueError:
            return default
    return default

def set_setting(key: str, value: Any):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO settings (key, value) VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
    """, (key, str(value)))
    conn.commit()
    conn.close()
