#include <Arduino.h>
#include "esp_camera.h"
#include "camera.h"
#include "../config/pins.h"
#include "../config/camConfig.h"

// ============================================================================
// INIT
// ============================================================================

bool Camera::init() {
    camera_config_t config;

    config.ledc_channel = LEDC_CHANNEL_0;
    config.ledc_timer   = LEDC_TIMER_0;

    // Pin assignments from AI-Thinker ESP32-CAM schematic
    config.pin_d0       = CAM_PIN_D0;
    config.pin_d1       = CAM_PIN_D1;
    config.pin_d2       = CAM_PIN_D2;
    config.pin_d3       = CAM_PIN_D3;
    config.pin_d4       = CAM_PIN_D4;
    config.pin_d5       = CAM_PIN_D5;
    config.pin_d6       = CAM_PIN_D6;
    config.pin_d7       = CAM_PIN_D7;
    config.pin_xclk     = CAM_PIN_XCLK;
    config.pin_pclk     = CAM_PIN_PCLK;
    config.pin_vsync    = CAM_PIN_VSYNC;
    config.pin_href     = CAM_PIN_HREF;
    config.pin_sccb_sda = CAM_PIN_SIOD;
    config.pin_sccb_scl = CAM_PIN_SIOC;
    config.pin_pwdn     = CAM_PIN_PWDN;
    config.pin_reset    = CAM_PIN_RESET;  // -1 = no hardware reset pin

    config.xclk_freq_hz = 20000000;       // 20 MHz XCLK
    config.pixel_format = PIXFORMAT_JPEG; // compressed JPEG output

    // PSRAM available on AI-Thinker ESP32-CAM (4MB)
    // Use larger buffers for better quality and stability
    if (psramFound()) {
        config.frame_size    = FRAMESIZE_SVGA;  // 800x600
        config.jpeg_quality  = JPEG_QUALITY;    // 12 from camConfig.h
        config.fb_count      = 2;               // double-buffer for stability
        config.grab_mode     = CAMERA_GRAB_LATEST;
        Serial.println("[Camera] PSRAM found — SVGA mode, double-buffer");
    } else {
        // Fallback if PSRAM is somehow unavailable
        config.frame_size    = FRAMESIZE_VGA;   // 640x480
        config.jpeg_quality  = 20;              // slightly lower quality
        config.fb_count      = 1;
        config.grab_mode     = CAMERA_GRAB_WHEN_EMPTY;
        Serial.println("[Camera] ⚠️ No PSRAM — VGA fallback mode");
    }

    esp_err_t err = esp_camera_init(&config);
    if (err != ESP_OK) {
        Serial.printf("[Camera] ❌ Initialisation failed: 0x%x\n", err);
        return false;
    }

    // Sensor tweaks for better image quality on OV2640
    sensor_t* sensor = esp_camera_sensor_get();
    if (sensor) {
        sensor->set_brightness(sensor, 0);    // neutral brightness
        sensor->set_saturation(sensor, 0);    // neutral saturation
        sensor->set_sharpness(sensor, 2);     // slight sharpness boost
        sensor->set_denoise(sensor, 1);       // noise reduction on
        sensor->set_whitebal(sensor, 1);      // auto white balance on
        sensor->set_awb_gain(sensor, 1);      // AWB gain on
        sensor->set_exposure_ctrl(sensor, 1); // auto exposure on
        sensor->set_aec2(sensor, 1);          // AEC DSP on
        sensor->set_gain_ctrl(sensor, 1);     // auto gain on
        sensor->set_bpc(sensor, 1);           // black pixel correction on
        sensor->set_wpc(sensor, 1);           // white pixel correction on
        sensor->set_raw_gma(sensor, 1);       // gamma correction on
        sensor->set_lenc(sensor, 1);          // lens correction on
    }

    Serial.println("[Camera] ✅ OV2640 initialised — SVGA 800x600 JPEG");
    return true;
}

// ============================================================================
// CAPTURE
// ============================================================================

bool Camera::capture() {
    // Release any previously held frame
    release();

    // Discard WARMUP_FRAMES to allow AE/AWB to stabilise
    for (int i = 0; i < WARMUP_FRAMES; i++) {
        camera_fb_t* warmup = esp_camera_fb_get();
        if (warmup) {
            esp_camera_fb_return(warmup);
        }
        delay(60);  // ~60ms per warmup frame
    }

    // Capture actual frame
    camera_fb_t* fb = esp_camera_fb_get();
    if (!fb) {
        Serial.println("[Camera] ❌ Frame capture failed — buffer null");
        return false;
    }

    if (fb->format != PIXFORMAT_JPEG) {
        Serial.println("[Camera] ❌ Unexpected pixel format — expected JPEG");
        esp_camera_fb_return(fb);
        return false;
    }

    _fb = (void*)fb;
    Serial.printf("[Camera] 📸 Captured — %u bytes (%ux%u)\n",
                  fb->len, fb->width, fb->height);
    return true;
}

// ============================================================================
// ACCESSORS
// ============================================================================

const uint8_t* Camera::getBuffer() const {
    if (!_fb) return nullptr;
    return ((camera_fb_t*)_fb)->buf;
}

size_t Camera::getSize() const {
    if (!_fb) return 0;
    return ((camera_fb_t*)_fb)->len;
}

bool Camera::hasFrame() const {
    return _fb != nullptr;
}

// ============================================================================
// RELEASE
// ============================================================================

void Camera::release() {
    if (_fb) {
        esp_camera_fb_return((camera_fb_t*)_fb);
        _fb = nullptr;
    }
}
