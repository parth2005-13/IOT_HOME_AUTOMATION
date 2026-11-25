import time
import json
import random
import threading
import sys
from pathlib import Path
import paho.mqtt.client as mqtt

# Add smart-home root to sys.path
CURRENT_DIR = Path(__file__).resolve().parent
PARENT_DIR = CURRENT_DIR.parent
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

import config

class ESP32Simulator:
    def __init__(self):
        self.light = "off"
        self.fan = "off"
        self.mode = "home"  # "home" | "away" | "sleep"
        
        # Sensor states
        self.motion = False
        self.lux = 150.0
        self.distance_cm = 120.0
        
        # Internal counters & timers
        self.last_motion_time = time.time()
        self.last_state_change_time = time.time()
        self.running = True
        self.auto_simulation = True
        
        # Client setup
        client_id = f"{config.MQTT_CLIENT_PREFIX}_esp32_sim_{random.randint(1000, 9999)}"
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
            print(f"[OK] [ESP32 Sim] Connected to MQTT Broker: {config.MQTT_BROKER}:{config.MQTT_PORT}")
            # Subscribe to command topic
            self.client.subscribe(config.TOPIC_CMD)
            print(f"[SUB] [ESP32 Sim] Subscribed to commands topic: {config.TOPIC_CMD}")
        else:
            print(f"[ERROR] [ESP32 Sim] MQTT Connection failed with code: {rc}")

    def on_disconnect(self, client, userdata, disconnect_flags_or_rc, reason_code_or_properties=None, properties=None):
        print("[WARN] [ESP32 Sim] Disconnected from MQTT Broker.")

    def on_message(self, client, userdata, msg):
        """Handle incoming command payload: {'device': '...', 'state': '...'}"""
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            device = payload.get("device")
            state = payload.get("state")
            
            print(f"[CMD] [ESP32 Sim] Received Command -> device: '{device}', state: '{state}'")

            if device == "light":
                if state in ["on", "off"]:
                    self.light = state
                    self.last_state_change_time = time.time()
                    print(f"[STATE] [ESP32 Sim] Light switched -> {self.light.upper()}")
            elif device == "fan":
                if state in ["on", "off"]:
                    self.fan = state
                    self.last_state_change_time = time.time()
                    print(f"[STATE] [ESP32 Sim] Fan switched -> {self.fan.upper()}")
            elif device == "mode":
                if state in ["home", "away", "sleep"]:
                    self.mode = state
                    print(f"[STATE] [ESP32 Sim] Mode changed -> {self.mode.upper()}")
                    if self.mode == "away":
                        self.light = "off"
                        self.fan = "off"
                    elif self.mode == "sleep":
                        self.light = "off"
            
            # Immediately publish sensor update to reflect command change
            self.publish_sensor_reading()

        except Exception as e:
            print(f"[WARN] [ESP32 Sim] Error parsing command message: {e}")

    def publish_sensor_reading(self):
        """Publishes sensor telemetry matching exact MQTT contract."""
        payload = {
            "ts": int(time.time()),
            "motion": bool(self.motion),
            "lux": round(float(self.lux), 1),
            "light": self.light,
            "fan": self.fan,
            "mode": self.mode,
            "distance_cm": round(float(self.distance_cm), 1)
        }
        self.client.publish(config.TOPIC_SENSORS, json.dumps(payload))

    def publish_alert(self, alert_type: str, severity: str = "high"):
        """Publishes alert matching exact MQTT contract."""
        payload = {
            "type": alert_type,
            "severity": severity,
            "ts": int(time.time())
        }
        self.client.publish(config.TOPIC_ALERTS, json.dumps(payload))
        print(f"[ALERT] [ESP32 Sim] ALERT PUBLISHED -> {alert_type.upper()} ({severity.upper()})")

    def simulate_sensor_drift(self):
        """Simulate dynamic environmental changes."""
        now = time.time()

        if self.auto_simulation:
            # 1. Simulate Lux (light intensity drift)
            hour = (time.localtime().tm_hour + time.localtime().tm_min / 60.0)
            if 6 <= hour <= 18:
                # Daylight curve + subtle noise
                base_lux = 300.0 * (1.0 - abs(hour - 12) / 6.0) + 50.0
            else:
                base_lux = 10.0
            
            # Additional light if light bulb is on
            if self.light == "on":
                base_lux += 200.0

            self.lux = max(2.0, base_lux + random.uniform(-10.0, 10.0))

            # 2. Simulate Motion & Presence
            if self.mode == "home":
                if random.random() < 0.25:
                    self.motion = True
                    self.last_motion_time = now
                    self.distance_cm = random.uniform(25.0, 48.0)
                else:
                    # Clear motion after 4 seconds of inactivity
                    if now - self.last_motion_time > 4.0:
                        self.motion = False
                        self.distance_cm = random.uniform(90.0, 160.0)

            elif self.mode == "away":
                # In away mode, motion is rare. If it happens, trigger intrusion!
                if random.random() < 0.05:
                    self.motion = True
                    self.distance_cm = random.uniform(20.0, 40.0)
                    self.publish_alert("intrusion", "high")
                else:
                    self.motion = False
                    self.distance_cm = random.uniform(110.0, 150.0)

            elif self.mode == "sleep":
                # Sleep mode: minimal movement
                self.motion = random.random() < 0.04
                self.distance_cm = random.uniform(80.0, 140.0)

            # 3. Check Forgotten Device (e.g. if device on for > timeout with no motion)
            if (self.light == "on" or self.fan == "on") and not self.motion:
                idle_duration = now - max(self.last_motion_time, self.last_state_change_time)
                if idle_duration > config.DEFAULT_TIMEOUT_SEC and random.random() < 0.05:
                    self.publish_alert("forgotten_device", "medium")

    def run(self):
        print("[*] Starting ESP32 Simulator...")
        print(f"[*] Connecting to {config.MQTT_BROKER}:{config.MQTT_PORT}...")
        self.client.connect(config.MQTT_BROKER, config.MQTT_PORT, config.MQTT_KEEPALIVE)
        self.client.loop_start()

        try:
            while self.running:
                self.simulate_sensor_drift()
                self.publish_sensor_reading()
                time.sleep(2.0)
        except KeyboardInterrupt:
            print("\n[*] Stopping ESP32 Simulator...")
        finally:
            self.publish_alert("offline", "low")
            self.client.loop_stop()
            self.client.disconnect()
            print("[*] ESP32 Simulator stopped.")

if __name__ == "__main__":
    sim = ESP32Simulator()
    sim.run()
