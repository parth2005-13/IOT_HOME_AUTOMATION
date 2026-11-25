#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <time.h>
#include "config.h"

// --- Global Network Objects ---
WiFiClient espClient;
PubSubClient mqttClient(espClient);

// --- Appliance States ---
bool stateLight = false;       // false: OFF, true: ON
bool stateFan = false;         // false: OFF, true: ON
String systemMode = "home";    // "home" | "away" | "sleep"

// --- Sensor Measurements ---
bool motionDetected = false;
float currentLux = 0.0;
float currentDistanceCm = 0.0;

// --- Timing and State Trackers ---
unsigned long lastTelemetryTime = 0;
unsigned long lastReconnectAttempt = 0;
unsigned long lastIntrusionAlertTime = 0;
const unsigned long INTRUSION_ALERT_COOLDOWN_MS = 10000; // Rate limit alerts to 10s

// --- Function Prototypes ---
void setupPins();
void connectWiFi();
void connectMQTT();
void syncNTP();
unsigned long getEpochTime();
float readUltrasonicDistance();
float readAmbientLux();
bool readPIRMotion();
void setLight(bool state);
void setFan(bool state);
void applySystemMode(const String& newMode);
void publishTelemetry();
void publishAlert(const char* alertType, const char* severity);
void mqttCallback(char* topic, byte* payload, unsigned int length);

// ==============================================================================
// SETUP ROUTINE
// ==============================================================================
void setup() {
    Serial.begin(115200);
    delay(500);
    Serial.println();


    // 1. Initialize GPIO pin modes
    setupPins();

    // 2. Connect to Wi-Fi Access Point
    connectWiFi();

    // 3. Synchronize internal clock via NTP
    syncNTP();

    // 4. Configure MQTT Client
    mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
    mqttClient.setCallback(mqttCallback);
    mqttClient.setBufferSize(512); // Ensure buffer fits JSON payloads
    mqttClient.setKeepAlive(MQTT_KEEPALIVE_SEC);

    Serial.println("[SETUP] Initialization complete. Entering main control loop.");
}

// ==============================================================================
// MAIN LOOP
// ==============================================================================
void loop() {
    // 1. Maintain Wi-Fi Connection
    if (WiFi.status() != WL_CONNECTED) {
        digitalWrite(PIN_STATUS_LED, LOW);
        connectWiFi();
    }

    // 2. Maintain MQTT Connection
    if (!mqttClient.connected()) {
        digitalWrite(PIN_STATUS_LED, LOW);
        unsigned long now = millis();
        if (now - lastReconnectAttempt > 5000) {
            lastReconnectAttempt = now;
            connectMQTT();
        }
    } else {
        digitalWrite(PIN_STATUS_LED, HIGH);
        mqttClient.loop();
    }

    // 3. Periodic Sensor Telemetry Acquisition & Publishing
    unsigned long currentMillis = millis();
    if (currentMillis - lastTelemetryTime >= TELEMETRY_INTERVAL_MS) {
        lastTelemetryTime = currentMillis;

        // Acquire sensor readings
        motionDetected = readPIRMotion();
        currentLux = readAmbientLux();
        currentDistanceCm = readUltrasonicDistance();

        // Check for security intrusion when in "away" mode
        if (systemMode == "away" && motionDetected) {
            if (currentMillis - lastIntrusionAlertTime > INTRUSION_ALERT_COOLDOWN_MS) {
                lastIntrusionAlertTime = currentMillis;
                Serial.println("[SECURITY] 🚨 Intrusion detected in AWAY mode!");
                publishAlert("intrusion", "high");
            }
        }

        // Publish telemetry packet if connected
        if (mqttClient.connected()) {
            publishTelemetry();
        }
    }
}

// ==============================================================================
// HARDWARE INITIALIZATION & CONTROL
// ==============================================================================
void setupPins() {
    pinMode(PIN_PIR, INPUT);
    pinMode(PIN_LDR, INPUT);
    pinMode(PIN_TRIG, OUTPUT);
    pinMode(PIN_ECHO, INPUT);

    pinMode(PIN_RELAY_LIGHT, OUTPUT);
    pinMode(PIN_RELAY_FAN, OUTPUT);
    pinMode(PIN_STATUS_LED, OUTPUT);

    // Initial safe states: Relays OFF
    digitalWrite(PIN_RELAY_LIGHT, RELAY_OFF);
    digitalWrite(PIN_RELAY_FAN, RELAY_OFF);
    digitalWrite(PIN_STATUS_LED, LOW);
    digitalWrite(PIN_TRIG, LOW);

    Serial.println("[PINS] Hardware GPIO pins initialized.");
}

void setLight(bool state) {
    stateLight = state;
    digitalWrite(PIN_RELAY_LIGHT, stateLight ? RELAY_ON : RELAY_OFF);
    Serial.printf("[ACTUATOR] Main Light set to: %s\n", stateLight ? "ON" : "OFF");
}

void setFan(bool state) {
    stateFan = state;
    digitalWrite(PIN_RELAY_FAN, stateFan ? RELAY_ON : RELAY_OFF);
    Serial.printf("[ACTUATOR] Room Fan set to: %s\n", stateFan ? "ON" : "OFF");
}

void applySystemMode(const String& newMode) {
    systemMode = newMode;
    Serial.printf("[MODE] System mode changed to: %s\n", systemMode.c_str());

    if (systemMode == "away") {
        setLight(false);
        setFan(false);
        Serial.println("[MODE] Away mode enforced: all appliances powered OFF.");
    } else if (systemMode == "sleep") {
        setLight(false);
        Serial.println("[MODE] Sleep mode enforced: lighting powered OFF.");
    }
}

// ==============================================================================
// SENSOR ACQUISITION ROUTINES
// ==============================================================================
float readUltrasonicDistance() {
    // Send 10 microsecond ultrasonic pulse
    digitalWrite(PIN_TRIG, LOW);
    delayMicroseconds(2);
    digitalWrite(PIN_TRIG, HIGH);
    delayMicroseconds(10);
    digitalWrite(PIN_TRIG, LOW);

    // Read echo pulse duration (microseconds) with safety timeout
    long duration = pulseIn(PIN_ECHO, HIGH, ULTRASONIC_TIMEOUT_US);
    if (duration <= 0) {
        return currentDistanceCm > 0 ? currentDistanceCm : 120.0; // Preserve last reading on miss
    }

    // Speed of sound = 343 m/s = 0.0343 cm/us (divided by 2 for round-trip)
    float distance = (duration * 0.0343) / 2.0;
    if (distance > 400.0) distance = 400.0;
    if (distance < 2.0) distance = 2.0;

    return round(distance * 10.0) / 10.0;
}

float readAmbientLux() {
    // 12-bit ADC on ESP32 (0 - 4095)
    int rawValue = analogRead(PIN_LDR);
    // Inverse relationship: High resistance in darkness (low voltage), low resistance in light
    // Approximate mapping: 0 -> 10 Lux, 4095 -> 1000 Lux
    float mappedLux = map(rawValue, 0, 4095, 10, 1000);
    return round(mappedLux * 10.0) / 10.0;
}

bool readPIRMotion() {
    return (digitalRead(PIN_PIR) == HIGH);
}

// ==============================================================================
// NETWORK, NTP & MQTT MANAGEMENT
// ==============================================================================
void connectWiFi() {
    if (WiFi.status() == WL_CONNECTED) return;

    Serial.printf("[WIFI] Connecting to SSID: %s ", WIFI_SSID);
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 20) {
        delay(500);
        Serial.print(".");
        digitalWrite(PIN_STATUS_LED, !digitalRead(PIN_STATUS_LED)); // Toggle LED while connecting
        attempts++;
    }

    if (WiFi.status() == WL_CONNECTED) {
        digitalWrite(PIN_STATUS_LED, HIGH);
        Serial.println("\n[WIFI] Connected successfully!");
        Serial.printf("[WIFI] Assigned IP Address: %s\n", WiFi.localIP().toString().c_str());
        Serial.printf("[WIFI] RSSI Signal Strength: %d dBm\n", WiFi.RSSI());
    } else {
        digitalWrite(PIN_STATUS_LED, LOW);
        Serial.println("\n[WIFI] Connection timeout. Retrying in next cycle...");
    }
}

void syncNTP() {
    Serial.println("[NTP] Synchronizing system clock via NTP (pool.ntp.org)...");
    configTime(0, 0, "pool.ntp.org", "time.nist.gov");

    time_t now = time(nullptr);
    int attempts = 0;
    while (now < 8 * 3600 * 2 && attempts < 15) {
        delay(500);
        Serial.print(".");
        now = time(nullptr);
        attempts++;
    }
    Serial.println();
    if (now > 8 * 3600 * 2) {
        Serial.printf("[NTP] Clock synchronized. Current Unix Epoch: %ld\n", (long)now);
    } else {
        Serial.println("[NTP] Time synchronization pending. Fallback to local clock.");
    }
}

unsigned long getEpochTime() {
    time_t now = time(nullptr);
    if (now > 100000) {
        return (unsigned long)now;
    }
    // Fallback if NTP is still syncing: millis offset
    return 1727780000 + (millis() / 1000);
}

void connectMQTT() {
    String clientId = String(MQTT_CLIENT_PREFIX) + String(random(1000, 9999), HEX);
    Serial.printf("[MQTT] Connecting to broker: %s:%d as %s...\n", MQTT_BROKER, MQTT_PORT, clientId.c_str());

    // Connect with Last Will and Testament (LWT) payload to publish offline status if connection drops
    const char* willTopic = TOPIC_ALERTS;
    const char* willPayload = "{\"type\":\"offline\",\"severity\":\"low\"}";

    if (mqttClient.connect(clientId.c_str(), willTopic, 0, false, willPayload)) {
        Serial.println("[MQTT] Connected successfully to HiveMQ broker!");
        // Subscribe to command topic
        mqttClient.subscribe(TOPIC_CMD);
        Serial.printf("[MQTT] Subscribed to command topic: %s\n", TOPIC_CMD);

        // Publish initial telemetry packet to declare presence
        publishTelemetry();
    } else {
        Serial.printf("[MQTT] Connection failed, rc=%d. Will retry in 5s.\n", mqttClient.state());
    }
}

// ==============================================================================
// MQTT MESSAGE HANDLER & SERIALIZATION
// ==============================================================================
void mqttCallback(char* topic, byte* payload, unsigned int length) {
    // Convert byte payload to null-terminated string
    char message[length + 1];
    memcpy(message, payload, length);
    message[length] = '\0';

    Serial.printf("[MQTT-IN] Topic [%s] -> Payload: %s\n", topic, message);

    // Parse incoming JSON payload
    JsonDocument doc;
    DeserializationError error = deserializeJson(doc, message);
    if (error) {
        Serial.printf("[MQTT-ERR] JSON deserialization failed: %s\n", error.c_str());
        return;
    }

    const char* device = doc["device"];
    const char* state = doc["state"];

    if (!device || !state) {
        Serial.println("[MQTT-ERR] Missing 'device' or 'state' key in payload.");
        return;
    }

    // Actuation logic
    if (strcmp(device, "light") == 0) {
        if (strcmp(state, "on") == 0) setLight(true);
        else if (strcmp(state, "off") == 0) setLight(false);
    } else if (strcmp(device, "fan") == 0) {
        if (strcmp(state, "on") == 0) setFan(true);
        else if (strcmp(state, "off") == 0) setFan(false);
    } else if (strcmp(device, "mode") == 0) {
        applySystemMode(String(state));
    }

    // Immediately publish updated telemetry packet to synchronize UI
    publishTelemetry();
}

void publishTelemetry() {
    JsonDocument doc;
    doc["ts"] = getEpochTime();
    doc["motion"] = motionDetected;
    doc["lux"] = currentLux;
    doc["distance_cm"] = currentDistanceCm;
    doc["light"] = stateLight ? "on" : "off";
    doc["fan"] = stateFan ? "on" : "off";
    doc["mode"] = systemMode;

    char buffer[256];
    size_t n = serializeJson(doc, buffer);

    if (mqttClient.publish(TOPIC_SENSORS, buffer, n)) {
        Serial.printf("[MQTT-OUT] Telemetry published: %s\n", buffer);
    } else {
        Serial.println("[MQTT-ERR] Failed to publish telemetry buffer.");
    }
}

void publishAlert(const char* alertType, const char* severity) {
    JsonDocument doc;
    doc["type"] = alertType;
    doc["severity"] = severity;
    doc["ts"] = getEpochTime();

    char buffer[128];
    size_t n = serializeJson(doc, buffer);

    if (mqttClient.publish(TOPIC_ALERTS, buffer, n)) {
        Serial.printf("[MQTT-ALERT] Alert dispatched: %s\n", buffer);
    } else {
        Serial.println("[MQTT-ERR] Failed to publish alert.");
    }
}