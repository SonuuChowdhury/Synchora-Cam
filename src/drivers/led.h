#pragma once

// ============================================================================
// Synchora-Cam LED Driver
// ============================================================================
// Manages two LEDs on the AI-Thinker ESP32-CAM:
//   - Flash LED  (GPIO 4)  : high-power white flash, active HIGH
//   - Status LED (GPIO 33) : small red indicator,    active LOW
// ============================================================================

class CamLed {
public:
    // Call once in App::init()
    void init(int flashPin, int statusPin);

    // Flash LED — white high-power flash
    void flashOn();
    void flashOff();

    // Status LED — active LOW red indicator
    void statusOn();
    void statusOff();

    // Call every loop tick — drives blink pattern based on connection state
    // wifiOk=true + wsOk=true  → solid ON  (no blink)
    // wifiOk=true + wsOk=false → slow blink (1000ms)
    // wifiOk=false             → fast blink  (200ms)
    void updateStatus(bool wifiOk, bool wsOk);

private:
    int _flashPin  = -1;
    int _statusPin = -1;

    unsigned long _lastBlink   = 0;
    bool          _statusState = false;
};
