#pragma once

// ============================================================================
// Synchora-Cam WiFi Service
// ============================================================================

class WifiService {
public:
    void init();
    void reconnectIfNeeded();
    bool isConnected();
};
