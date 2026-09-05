#include <Arduino.h>
#include "App/app.h"

void setup() {
    Serial.begin(115200);
    App::init();
}

void loop() {
    App::run();
}
