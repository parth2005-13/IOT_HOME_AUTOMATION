import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory for smart-home
BASE_DIR = Path(__file__).resolve().parent

# Load .env file from the smart-home directory
load_dotenv(dotenv_path=BASE_DIR / ".env")

# MQTT Configuration
MQTT_BROKER = os.getenv("MQTT_BROKER", "broker.hivemq.com")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_CLIENT_PREFIX = os.getenv("MQTT_CLIENT_PREFIX", "smarthome_user")
MQTT_KEEPALIVE = int(os.getenv("MQTT_KEEPALIVE", "60"))

# MQTT Topics (Standard Contract)
TOPIC_SENSORS = os.getenv("TOPIC_SENSORS", "home/room1/sensors")
TOPIC_CMD = os.getenv("TOPIC_CMD", "home/room1/cmd")
TOPIC_ALERTS = os.getenv("TOPIC_ALERTS", "home/alerts")

# Database Configuration
DB_NAME = os.getenv("DB_PATH", "smart_home.db")
DB_PATH = BASE_DIR / DB_NAME

# Hardware defaults (fallback if not configured in settings table)
DEFAULT_LIGHT_WATTS = float(os.getenv("DEFAULT_LIGHT_WATTS", "15.0"))
DEFAULT_FAN_WATTS = float(os.getenv("DEFAULT_FAN_WATTS", "75.0"))
DEFAULT_TARIFF_PER_KWH = float(os.getenv("DEFAULT_TARIFF_PER_KWH", "8.0"))
DEFAULT_LUX_THRESHOLD = float(os.getenv("DEFAULT_LUX_THRESHOLD", "200.0"))
DEFAULT_TIMEOUT_SEC = int(os.getenv("DEFAULT_TIMEOUT_SEC", "30"))
DEFAULT_INTRUSION_DISTANCE_THRESHOLD = 50.0  # cm
