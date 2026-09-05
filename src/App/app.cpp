#include <Arduino.h>
#include "app.h"
#include "../config/pins.h"
#include "../config/camConfig.h"
#include "../drivers/led.h"
#include "../drivers/camera.h"
#include "../services/wifiService.h"
#include "../services/webSocketService.h"

// ============================================================================
// HARDWARE & SERVICES
// ============================================================================

static CamLed              led;
static Camera              camera;
static WifiService         wifi;
static CamWebSocketService webSocket;

// ============================================================================
// STATE
// ============================================================================

static bool captureRequested = false;   // set by onMessage when CAPTURE_NOW arrives

// ============================================================================
// WEBSOCKET CALLBACKS
// ============================================================================

void onCamConnected(const char* message) {
    Serial.println("[App] 🔗 Connected to Synchora-MS — sending CAM TOKEN...");
    String tokenMsg = "{\"event\":\"TOKEN\",\"user_id\":\"";
    tokenMsg += CAM_DEVICE_ID;
    tokenMsg += "\"}";
    webSocket.sendMessage(tokenMsg.c_str());
}

void onCamDisconnected(const char* message) {
    Serial.println("[App] ❌ Disconnected from Synchora-MS");
    captureRequested = false;
}

void onCamMessage(const char* message) {
    Serial.printf("[App] 📨 Message: %s\n", message);

    if (strstr(message, "\"CAPTURE_NOW\"")) {
        Serial.println("[App] 📸 CAPTURE_NOW received — queuing capture");
        captureRequested = true;
    }
}

void onCamError(const char* message) {
    Serial.printf("[App] ⚠️ WebSocket error: %s\n", message);
}

// ============================================================================
// CAPTURE HANDLER
// ============================================================================

void handleCapture() {
    if (!captureRequested) return;
    captureRequested = false;

    if (!webSocket.isConnected()) {
        Serial.println("[App] ❌ Capture aborted — WebSocket not connected");
        return;
    }

    Serial.println("[App] 📸 Capture sequence starting...");

    // 1. Flash ON
    led.flashOn();
    delay(FLASH_PULSE_MS);

    // 2. Capture JPEG (includes WARMUP_FRAMES discard internally)
    bool ok = camera.capture();

    // 3. Flash OFF immediately after capture
    led.flashOff();

    if (!ok || !camera.hasFrame()) {
        Serial.println("[App] ❌ Capture failed — no frame");
        webSocket.sendMessage("{\"event\":\"CAPTURE_FAILED\"}");
        return;
    }

    // 4. Send JPEG binary over WebSocket
    Serial.printf("[App] 📤 Sending JPEG (%u bytes) to server...\n",
                  (unsigned)camera.getSize());
    webSocket.sendBinary(camera.getBuffer(), camera.getSize());

    // 5. Release PSRAM frame buffer
    camera.release();
    Serial.println("[App] ✅ JPEG sent and frame buffer released");
}

// ============================================================================
// INIT
// ============================================================================

void App::init() {
    delay(500);
    Serial.println("\n\n[App] 🚀 Synchora-Cam initialising...");

    // LEDs
    Serial.println("[App] 💡 Initialising LEDs...");
    led.init(FLASH_LED_PIN, STATUS_LED_PIN);

    // WiFi
    Serial.println("[App] 📡 Starting WiFi...");
    wifi.init();

    // Camera
    Serial.println("[App] 📷 Initialising OV2640 camera...");
    if (!camera.init()) {
        Serial.println("[App] ❌ Camera init failed — halting");
        // Rapid flash to signal hardware error
        while (true) {
            led.flashOn();  delay(100);
            led.flashOff(); delay(100);
        }
    }

    // WebSocket
    Serial.println("[App] 🔌 Starting WebSocket...");
    webSocket.onConnected(onCamConnected);
    webSocket.onDisconnected(onCamDisconnected);
    webSocket.onMessage(onCamMessage);
    webSocket.onError(onCamError);
    webSocket.init();

    Serial.println("[App] ✅ Synchora-Cam ready!\n");
}

// ============================================================================
// RUN (main loop)
// ============================================================================

void App::run() {
    wifi.reconnectIfNeeded();
    webSocket.run();

    // Drive red LED blink pattern based on connection state
    led.updateStatus(wifi.isConnected(), webSocket.isConnected());

    // Handle pending CAPTURE_NOW request
    handleCapture();
}
