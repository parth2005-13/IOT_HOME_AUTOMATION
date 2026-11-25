import time
import json
import random
from datetime import datetime
import sys
from pathlib import Path
import paho.mqtt.client as mqtt

# Add smart-home root to sys.path
CURRENT_DIR = Path(__file__).resolve().parent
PARENT_DIR = CURRENT_DIR.parent
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

import config
from backend.db import (
    init_db,
    insert_sensor_reading,
    insert_device_event,
    insert_alert,
    update_energy_log,
    get_setting_float
)

class MQTTListener:
    def __init__(self):
        # Initialize DB schema
        init_db()

        # State tracking for delta energy calculation and transition events
        self.last_sensor_time = None
        self.prev_light = None
        self.prev_fan = None
        self.prev_mode = None
        self.running = True

        client_id = f"{config.MQTT_CLIENT_PREFIX}_backend_listener_{random.randint(1000, 9999)}"
        try:
            from paho.mqtt.enums import CallbackAPIVersion
            self.client = mqtt.Client(CallbackAPIVersion.VERSION2, client_id=client_id)
        except (ImportError, AttributeError):
            self.client = mqtt.Client(client_id=client_id)

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

    def on_connect(self, client, userdata, flags, rc, properties=None):
        rc_code = rc if isinstance(rc, int) else getattr(rc, 'value', 0)
        if rc_code == 0:
            print(f"[OK] [MQTT Listener] Connected to {config.MQTT_BROKER}:{config.MQTT_PORT}")
            # Subscribe to all relevant topics
            self.client.subscribe(config.TOPIC_SENSORS)
            self.client.subscribe(config.TOPIC_CMD)
            self.client.subscribe(config.TOPIC_ALERTS)
            print(f"[SUB] [MQTT Listener] Subscribed to:\n  - {config.TOPIC_SENSORS}\n  - {config.TOPIC_CMD}\n  - {config.TOPIC_ALERTS}")
        else:
            print(f"[ERROR] [MQTT Listener] Connection failed with code {rc}")

    def on_disconnect(self, client, userdata, disconnect_flags_or_rc, reason_code_or_properties=None, properties=None):
        print("[WARN] [MQTT Listener] Disconnected from broker.")

    def on_message(self, client, userdata, msg):
        topic = msg.topic
        payload_str = msg.payload.decode("utf-8")

        try:
            payload = json.loads(payload_str)
        except Exception as e:
            print(f"[WARN] [MQTT Listener] Failed to decode JSON from topic {topic}: {e}")
            return

        now_ts = int(time.time())

        # 1. Handle Sensor Readings
        if topic == config.TOPIC_SENSORS:
            self.handle_sensor_reading(payload, now_ts)

        # 2. Handle Commands
        elif topic == config.TOPIC_CMD:
            self.handle_command(payload, now_ts)

        # 3. Handle Alerts
        elif topic == config.TOPIC_ALERTS:
            self.handle_alert(payload, now_ts)

    def handle_sensor_reading(self, payload: dict, now_ts: int):
        ts = payload.get("ts", now_ts)
        motion = bool(payload.get("motion", False))
        lux = float(payload.get("lux", 0.0))
        distance_cm = float(payload.get("distance_cm", 0.0))
        light = str(payload.get("light", "off")).lower()
        fan = str(payload.get("fan", "off")).lower()
        mode = str(payload.get("mode", "home")).lower()

        # Insert into sensor_readings table
        insert_sensor_reading(ts, motion, lux, distance_cm, light, fan, mode)

        # Detect and log state transitions
        if self.prev_light is not None and self.prev_light != light:
            insert_device_event(ts, "light", light, source="auto")
        if self.prev_fan is not None and self.prev_fan != fan:
            insert_device_event(ts, "fan", fan, source="auto")
        if self.prev_mode is not None and self.prev_mode != mode:
            insert_device_event(ts, "mode", mode, source="auto")

        self.prev_light = light
        self.prev_fan = fan
        self.prev_mode = mode

        # Energy consumption computation
        if self.last_sensor_time is not None:
            dt = ts - self.last_sensor_time
            # Discard unreasonable gaps (e.g. if offline for hours)
            if 0 < dt <= 10.0:
                today_str = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
                light_watts = get_setting_float("light_watts", config.DEFAULT_LIGHT_WATTS)
                fan_watts = get_setting_float("fan_watts", config.DEFAULT_FAN_WATTS)

                if light == "on":
                    on_mins = dt / 60.0
                    kwh = (light_watts * (dt / 3600.0)) / 1000.0
                    update_energy_log(today_str, "light", on_mins, kwh)

                if fan == "on":
                    on_mins = dt / 60.0
                    kwh = (fan_watts * (dt / 3600.0)) / 1000.0
                    update_energy_log(today_str, "fan", on_mins, kwh)

        self.last_sensor_time = ts

    def handle_command(self, payload: dict, now_ts: int):
        device = payload.get("device")
        state = payload.get("state")
        source = payload.get("source", "dashboard")

        if device and state:
            print(f"[CMD] [MQTT Listener] Recorded Command: {device} -> {state} (source: {source})")
            insert_device_event(now_ts, device, state, source=source)

    def handle_alert(self, payload: dict, now_ts: int):
        alert_type = payload.get("type", "unknown")
        severity = payload.get("severity", "medium")
        ts = payload.get("ts", now_ts)

        print(f"[ALERT] [MQTT Listener] Received Alert: {alert_type.upper()} ({severity.upper()})")
        insert_alert(ts, alert_type, severity)

    def run(self):
        print("[*] Starting MQTT Backend Listener...")
        print(f"[*] Connecting to broker: {config.MQTT_BROKER}:{config.MQTT_PORT}")
        self.client.connect(config.MQTT_BROKER, config.MQTT_PORT, config.MQTT_KEEPALIVE)
        self.client.loop_start()

        try:
            while self.running:
                time.sleep(1.0)
        except KeyboardInterrupt:
            print("\n[*] Stopping MQTT Listener...")
        finally:
            self.client.loop_stop()
            self.client.disconnect()
            print("[*] MQTT Listener stopped.")

if __name__ == "__main__":
    listener = MQTTListener()
    listener.run()
