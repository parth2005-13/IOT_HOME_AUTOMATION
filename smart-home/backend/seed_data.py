import time
import random
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add smart-home root to sys.path
CURRENT_DIR = Path(__file__).resolve().parent
PARENT_DIR = CURRENT_DIR.parent
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

import config
from backend.db import (
    init_db,
    get_connection,
    get_setting_float,
    insert_sensor_reading,
    insert_device_event,
    insert_alert,
    update_energy_log
)

def seed_database():
    print("[*] Initializing database schema and settings...")
    init_db()

    conn = get_connection()
    cursor = conn.cursor()

    # Clear previous seed data for clean demonstration
    cursor.execute("DELETE FROM sensor_readings")
    cursor.execute("DELETE FROM device_events")
    cursor.execute("DELETE FROM alerts")
    cursor.execute("DELETE FROM energy_log")
    conn.commit()

    light_watts = get_setting_float("light_watts", config.DEFAULT_LIGHT_WATTS)
    fan_watts = get_setting_float("fan_watts", config.DEFAULT_FAN_WATTS)

    now = datetime.now()
    print("[*] Generating 7 days of realistic historical data...")

    # 1. Generate Energy Log for the past 7 days
    for days_ago in range(7, -1, -1):
        target_date = (now - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        
        # Light: on mostly in evening (2 to 5 hours = 120 - 300 minutes)
        light_mins = random.uniform(120.0, 320.0)
        light_kwh = (light_watts * (light_mins / 60.0)) / 1000.0
        update_energy_log(target_date, "light", round(light_mins, 2), round(light_kwh, 4))

        # Fan: on during warmer periods (3 to 7 hours = 180 - 420 minutes)
        fan_mins = random.uniform(180.0, 420.0)
        fan_kwh = (fan_watts * (fan_mins / 60.0)) / 1000.0
        update_energy_log(target_date, "fan", round(fan_mins, 2), round(fan_kwh, 4))

    # 2. Generate Device Events for the past 7 days
    events_templates = [
        ("light", "on", "auto"),
        ("fan", "on", "dashboard"),
        ("mode", "away", "dashboard"),
        ("light", "off", "auto"),
        ("mode", "home", "dashboard"),
        ("light", "on", "dashboard"),
        ("fan", "off", "auto"),
        ("mode", "sleep", "dashboard")
    ]

    for days_ago in range(7, -1, -1):
        day_time = now - timedelta(days=days_ago)
        num_events = random.randint(3, 6)
        for _ in range(num_events):
            hour = random.randint(6, 23)
            minute = random.randint(0, 59)
            event_dt = day_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
            dev, st, src = random.choice(events_templates)
            insert_device_event(int(event_dt.timestamp()), dev, st, src)

    # 3. Generate Sensor Readings (samples every 30 mins over past 48 hours for smooth charts)
    start_time = now - timedelta(hours=48)
    curr = start_time
    while curr <= now:
        ts = int(curr.timestamp())
        hour = curr.hour

        # Realistic daylight curve
        if 6 <= hour <= 18:
            # Daytime: lux peaks around noon
            solar_factor = 1.0 - abs(hour - 12) / 6.0
            lux = max(10.0, solar_factor * 600.0 + random.uniform(-30, 40))
        else:
            # Nighttime: low ambient light
            lux = max(0.0, random.uniform(2.0, 15.0))

        # Motion & distance behavior
        is_day = 8 <= hour <= 22
        motion = (random.random() < 0.45) if is_day else (random.random() < 0.08)
        distance_cm = random.uniform(20.0, 45.0) if motion else random.uniform(100.0, 180.0)

        # Mode and state
        if 23 <= hour or hour < 7:
            mode = "sleep"
            light = "off"
            fan = "on" if random.random() < 0.7 else "off"
        elif 9 <= hour <= 17 and random.random() < 0.4:
            mode = "away"
            light = "off"
            fan = "off"
        else:
            mode = "home"
            light = "on" if (lux < 150 and motion) else "off"
            fan = "on" if random.random() < 0.5 else "off"

        insert_sensor_reading(ts, motion, round(lux, 1), round(distance_cm, 1), light, fan, mode)
        curr += timedelta(minutes=30)

    # 4. Generate realistic Alerts
    sample_alerts = [
        (int((now - timedelta(days=4, hours=3)).timestamp()), "forgotten_device", "medium", 1),
        (int((now - timedelta(days=2, hours=14)).timestamp()), "intrusion", "high", 1),
        (int((now - timedelta(days=1, hours=8)).timestamp()), "offline", "low", 1),
        (int((now - timedelta(hours=5)).timestamp()), "forgotten_device", "medium", 0),
        (int((now - timedelta(minutes=45)).timestamp()), "intrusion", "high", 0),
    ]

    for ts, a_type, severity, ack in sample_alerts:
        cursor.execute("""
            INSERT INTO alerts (ts, type, severity, acknowledged)
            VALUES (?, ?, ?, ?)
        """, (ts, a_type, severity, ack))

    conn.commit()
    conn.close()
    print("[SUCCESS] Seed data successfully populated in SQLite database!")

if __name__ == "__main__":
    seed_database()
