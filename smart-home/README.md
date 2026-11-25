# 🏠 IoT Smart Home Automation & Security Dashboard

A comprehensive, production-grade IoT Smart Home Automation & Energy Management System powered by **ESP32 (with Python simulator)**, **MQTT**, **SQLite**, and **Streamlit**.

---

## 🏗️ Architecture Overview

```
                   +-----------------------------+
                   |  ESP32 Hardware / Simulator |
                   |     (simulator/esp32_sim)   |
                   +--------------+--------------+
                                  |
                   MQTT (home/room1/sensors, cmd, alerts)
                                  |
                   +--------------v--------------+
                   |     MQTT Message Broker     |
                   |   (HiveMQ / Mosquitto)      |
                   +--------------+--------------+
                                  |
                                  +------------------------------------+
                                  |                                    |
                    +-------------v-------------+       +--------------v--------------+
                    |    Backend MQTT Listener  |       |     Streamlit Dashboard     |
                    | (backend/mqtt_listener.py)|       |   (dashboard/app.py & pages)|
                    +-------------+-------------+       +--------------+--------------+
                                  |                                    ^
                             Writes To                             Reads From
                                  |                                    |
                                  +-------------> SQLite <-------------+
                                              (smart_home.db)
```

---

## 📁 Directory Structure

```
smart-home/
├── .env.example              # Example environment configuration
├── .env                      # Active configuration (MQTT broker, defaults)
├── requirements.txt          # Python dependencies
├── README.md                 # Complete documentation
├── config.py                 # Centralized configuration & environment loader
├── simulator/
│   ├── __init__.py
│   └── esp32_sim.py          # ESP32 hardware emulator
├── backend/
│   ├── __init__.py
│   ├── db.py                 # SQLite schema, queries, and energy calculators
│   ├── mqtt_listener.py      # MQTT subscriber daemon & state tracker
│   └── seed_data.py          # 7-day realistic data generator
└── dashboard/
    ├── app.py                # Streamlit entry point (Live Status & Control)
    ├── components.py         # Shared UI cards, CSS, and non-blocking MQTT publisher
    └── pages/
        ├── 1_Energy.py       # Energy consumption & electricity cost analytics
        ├── 2_Alerts.py       # Security & system alerts management
        └── 3_Settings.py     # Calibration & dynamic threshold configuration
```

---

## 🚀 Quick Start Guide

### 1. Install Dependencies
```bash
cd smart-home
pip install -r requirements.txt
```

### 2. Seed Historical Data (Optional but Recommended)
Populate 7 days of realistic sensor telemetry, energy logs, device events, and alerts:
```bash
python backend/seed_data.py
```

### 3. Launch the Backend MQTT Listener
```bash
python backend/mqtt_listener.py
```

### 4. Launch the ESP32 Simulator
In a second terminal:
```bash
python simulator/esp32_sim.py
```

### 5. Launch the Streamlit Dashboard
In a third terminal:
```bash
streamlit run dashboard/app.py
```

Open your browser at `http://localhost:8501`.

---

## 📜 MQTT Contract

### 1. Device Telemetry (`home/room1/sensors`)
Published by ESP32 / Simulator every 2 seconds:
```json
{
  "ts": 1727690000,
  "motion": true,
  "lux": 120.5,
  "light": "on",
  "fan": "off",
  "mode": "home",
  "distance_cm": 84.0
}
```

### 2. Device Commands (`home/room1/cmd`)
Published by Dashboard / Telegram Bot / Automation Engine:
```json
{"device": "light", "state": "on"}
{"device": "fan", "state": "off"}
{"device": "mode", "state": "home"} // "home" | "away" | "sleep"
```

### 3. System Alerts (`home/alerts`)
Published when events occur:
```json
{
  "type": "intrusion",       // "intrusion" | "forgotten_device" | "offline"
  "severity": "high",        // "high" | "medium" | "low"
  "ts": 1727690000
}
```

---

## 🔌 Transitioning to Real ESP32 Hardware

When your physical ESP32 board and sensors are wired up:
1. Simply flash your ESP32 with the MQTT client code pointing to the same broker (e.g. `broker.hivemq.com` or local Mosquitto).
2. The Streamlit dashboard, SQLite database, and MQTT backend listener will work seamlessly with zero software modifications!
