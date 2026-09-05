#include <Arduino.h>
#include <WiFi.h>
#include <WebSocketsClient.h>
#include "webSocketService.h"
#include "../config/webSocket.h"

static WebSocketsClient _ws;
CamWebSocketService* CamWebSocketService::_instance = nullptr;

// ============================================================================
// EVENT HANDLER
// ============================================================================

void camWsEventHandler(WStype_t type, uint8_t* payload, size_t length) {
    if (!CamWebSocketService::_instance) return;
    CamWebSocketService* svc = CamWebSocketService::_instance;

    switch (type) {
        case WStype_DISCONNECTED:
            Serial.println("[WS-Cam] ❌ Disconnected from server");
            svc->_state = WsState::DISCONNECTED;
            if (svc->_onDisconnectedCb) svc->_onDisconnectedCb("Disconnected");
            break;

        case WStype_CONNECTED:
            Serial.println("[WS-Cam] ✅ Connected to server");
            svc->_state = WsState::CONNECTED;
            if (svc->_onConnectedCb) svc->_onConnectedCb("Connected");
            break;

        case WStype_TEXT: {
            char* msg = (char*)malloc(length + 1);
            if (msg) {
                memcpy(msg, payload, length);
                msg[length] = '\0';
                Serial.printf("[WS-Cam] 📨 Received: %s\n", msg);
                if (svc->_onMessageCb) svc->_onMessageCb(msg);
                free(msg);
            }
            break;
        }

        case WStype_ERROR:
            Serial.println("[WS-Cam] ⚠️ WebSocket error");
            svc->_state = WsState::ERROR;
            if (svc->_onErrorCb) svc->_onErrorCb("WebSocket error");
            break;

        default:
            break;
    }
}

// ============================================================================
// INIT
// ============================================================================

void CamWebSocketService::init() {
    _instance = this;
    _state    = WsState::CONNECTING;

    const char* url = WEBSOCKET_URL;
    Serial.printf("[WS-Cam] 🔌 Connecting to %s\n", url);

    bool isSecure = strncmp(url, "wss://", 6) == 0;
    const char* hostStart = isSecure ? url + 6 : url + 5;

    char host[256];
    int i = 0;
    while (hostStart[i] != '/' && hostStart[i] != '\0' && i < 255) {
        host[i] = hostStart[i];
        i++;
    }
    host[i] = '\0';
    const char* path = hostStart[i] == '/' ? &hostStart[i] : "/";

    if (isSecure) {
        _ws.beginSSL(host, WEBSOCKET_PORT, path, (const char*)NULL);
        Serial.println("[WS-Cam] Using WSS (secure)");
    } else {
        _ws.begin(host, 80, path);
        Serial.println("[WS-Cam] Using WS (non-secure)");
    }

    _ws.setExtraHeaders("ngrok-skip-browser-warning: true\r\nUser-Agent: ESP32-CAM/1.0\r\n");
    _ws.onEvent(camWsEventHandler);
    _ws.setReconnectInterval(1000);
}

// ============================================================================
// RUN
// ============================================================================

void CamWebSocketService::run() {
    _ws.loop();
}

// ============================================================================
// STATUS
// ============================================================================

bool CamWebSocketService::isConnected() {
    return _state == WsState::CONNECTED;
}

// ============================================================================
// SEND METHODS
// ============================================================================

void CamWebSocketService::sendEvent(const char* eventType) {
    if (!isConnected()) return;
    String json = "{\"event\":\"" + String(eventType) + "\"}";
    sendMessage(json.c_str());
}

void CamWebSocketService::sendMessage(const char* jsonMessage) {
    if (!isConnected()) {
        Serial.println("[WS-Cam] ❌ Cannot send — disconnected");
        return;
    }
    Serial.printf("[WS-Cam] 📤 %s\n", jsonMessage);
    _ws.sendTXT(jsonMessage);
}

void CamWebSocketService::sendBinary(const uint8_t* data, size_t length) {
    if (!isConnected()) return;
    Serial.printf("[WS-Cam] 📤 Sending binary JPEG — %u bytes\n", (unsigned)length);
    _ws.sendBIN(data, length);
}

// ============================================================================
// CALLBACKS
// ============================================================================

void CamWebSocketService::onConnected(WsTextCb cb)    { _onConnectedCb    = cb; }
void CamWebSocketService::onDisconnected(WsTextCb cb) { _onDisconnectedCb = cb; }
void CamWebSocketService::onMessage(WsTextCb cb)      { _onMessageCb      = cb; }
void CamWebSocketService::onError(WsTextCb cb)        { _onErrorCb        = cb; }
