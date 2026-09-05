#include <Arduino.h>
#include "led.h"

// ============================================================================
// INIT
// ============================================================================

void CamLed::init(int flashPin, int statusPin) {
    _flashPin  = flashPin;
    _statusPin = statusPin;

    pinMode(_flashPin,  OUTPUT);
    pinMode(_statusPin, OUTPUT);

    flashOff();    // start with flash off
    statusOff();   // start with status off
}

// ============================================================================
// FLASH LED — active HIGH
// ============================================================================

void CamLed::flashOn() {
    if (_flashPin >= 0) digitalWrite(_flashPin, HIGH);
}

void CamLed::flashOff() {
    if (_flashPin >= 0) digitalWrite(_flashPin, LOW);
}

// ============================================================================
// STATUS LED — active LOW (LOW = ON, HIGH = OFF)
// ============================================================================

void CamLed::statusOn() {
    if (_statusPin >= 0) digitalWrite(_statusPin, LOW);   // active LOW
}

void CamLed::statusOff() {
    if (_statusPin >= 0) digitalWrite(_statusPin, HIGH);  // active LOW
}

// ============================================================================
// STATUS UPDATE — driven each loop tick
//   wifiOk=false            → fast blink  200ms
//   wifiOk=true, wsOk=false → slow blink 1000ms
//   wifiOk=true, wsOk=true  → solid ON   (no blink)
// ============================================================================

void CamLed::updateStatus(bool wifiOk, bool wsOk) {
    if (wifiOk && wsOk) {
        // Both connected — solid ON
        statusOn();
        _statusState = true;
        return;
    }

    unsigned long now      = millis();
    unsigned long interval = wifiOk ? 1000UL : 200UL;  // slow or fast blink

    if (now - _lastBlink >= interval) {
        _lastBlink   = now;
        _statusState = !_statusState;
        _statusState ? statusOn() : statusOff();
    }
}
