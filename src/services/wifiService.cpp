#include <Arduino.h>
#include <WiFi.h>
#include "wifiService.h"
#include "../config/wifiConfig.h"

// ============================================================================
// INIT
// ============================================================================

void WifiService::init() {
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASS);

    Serial.printf("[WiFi] Connecting to \"%s\"", WIFI_SSID);

    unsigned long start = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - start < 15000) {
        delay(500);
        Serial.print(".");
    }

    if (WiFi.status() == WL_CONNECTED) {
        Serial.printf("\n[WiFi] ✅ Connected — IP: %s\n", WiFi.localIP().toString().c_str());
    } else {
        Serial.println("\n[WiFi] ⚠️ Could not connect — will retry in loop");
    }
}

// ============================================================================
// RECONNECT
// ============================================================================

void WifiService::reconnectIfNeeded() {
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("[WiFi] 🔄 Reconnecting...");
        WiFi.disconnect();
        WiFi.begin(WIFI_SSID, WIFI_PASS);
    }
}

// ============================================================================
// STATUS
// ============================================================================

bool WifiService::isConnected() {
    return WiFi.status() == WL_CONNECTED;
}
