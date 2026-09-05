#pragma once

#include <WebSocketsClient.h>

// ============================================================================
// Synchora-Cam WebSocket Service
// ============================================================================
// Same architecture as Synchora-Device webSocketService.
// Manages the single persistent connection to Synchora-MS.
// ============================================================================

enum class WsState { DISCONNECTED, CONNECTING, CONNECTED, ERROR };

typedef void (*WsTextCb)(const char* message);

void camWsEventHandler(WStype_t type, uint8_t* payload, size_t length);

class CamWebSocketService {
public:
    void init();
    void run();
    bool isConnected();

    void sendMessage(const char* jsonMessage);
    void sendEvent(const char* eventType);
    void sendBinary(const uint8_t* data, size_t length);

    void onConnected(WsTextCb cb);
    void onDisconnected(WsTextCb cb);
    void onMessage(WsTextCb cb);
    void onError(WsTextCb cb);

    static CamWebSocketService* _instance;

private:
    friend void camWsEventHandler(WStype_t type, uint8_t* payload, size_t length);

    WsState    _state          = WsState::DISCONNECTED;
    WsTextCb   _onConnectedCb  = nullptr;
    WsTextCb   _onDisconnectedCb = nullptr;
    WsTextCb   _onMessageCb    = nullptr;
    WsTextCb   _onErrorCb      = nullptr;
};
