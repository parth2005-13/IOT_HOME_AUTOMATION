#pragma once

// ==============================================================================
// 🏠 IoT Smart Home Automation & Energy Management System - ESP32 Firmware Config
// Author: Parth Mishra (Roll No: 2400320100789)
// Guide: Ms. Anupam | Dept. of Computer Science & Engineering
// ==============================================================================

// --- Wi-Fi Configuration ---
// Update these credentials to connect to your home/mobile hotspot Wi-Fi network
#define WIFI_SSID           "YOUR_WIFI_SSID"
#define WIFI_PASSWORD       "YOUR_WIFI_PASSWORD"

// --- MQTT Broker Configuration ---
#define MQTT_BROKER         "broker.hivemq.com"
#define MQTT_PORT           1883
#define MQTT_CLIENT_PREFIX  "esp32_smarthome_"
#define MQTT_KEEPALIVE_SEC  60

// --- MQTT Topics (Exact Contract with Dashboard & Backend) ---
#define TOPIC_SENSORS       "home/room1/sensors"
#define TOPIC_CMD           "home/room1/cmd"
#define TOPIC_ALERTS        "home/alerts"

// --- Hardware Pin Assignments (Per IEEE 830 Specification) ---
#define PIN_PIR             13   // HC-SR501 PIR Motion Sensor (Digital In)
#define PIN_LDR             34   // LDR Light Sensor (Analog In, ADC1_CH6)
#define PIN_TRIG            5    // HC-SR04 Ultrasonic Trigger (Digital Out)
#define PIN_ECHO            18   // HC-SR04 Ultrasonic Echo (Digital In)
#define PIN_RELAY_LIGHT     22   // 5V Relay Channel 1 - Light (Digital Out)
#define PIN_RELAY_FAN       23   // 5V Relay Channel 2 - Fan (Digital Out)
#define PIN_STATUS_LED      2    // On-board Status LED (Digital Out)

// --- Relay Trigger Logic ---
// Most common relay modules are Active LOW (LOW = Relay ON / Closed, HIGH = Relay OFF / Open).
// If your relay module is Active HIGH, change these definitions.
#define RELAY_ON            LOW
#define RELAY_OFF           HIGH

// --- Operational Timing Parameters ---
#define TELEMETRY_INTERVAL_MS   2000    // Telemetry publish interval (2 seconds)
#define ULTRASONIC_TIMEOUT_US   25000   // Max wait time for echo pulse (~400cm max range)
#define PIR_DEBOUNCE_TIME_MS    1000    // Debounce guard
