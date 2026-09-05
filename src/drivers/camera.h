#pragma once

#include <stddef.h>
#include <stdint.h>

// ============================================================================
// Synchora-Cam — OV2640 Camera Driver
// ============================================================================
// Wraps esp_camera.h with a clean interface for capture + PSRAM management.
// Resolution: SVGA (800x600), JPEG quality 12 (~30-60 KB per frame).
// ============================================================================

class Camera {
public:
    // Configure all pins and initialise the OV2640 sensor.
    // Returns true on success, false on hardware failure.
    bool init();

    // Discard WARMUP_FRAMES to allow AE/AWB to stabilise,
    // then capture one JPEG frame into an internal fb pointer.
    // Returns true if capture succeeded, false on error.
    bool capture();

    // Pointer to JPEG byte buffer (valid after capture(), null if no frame).
    const uint8_t* getBuffer() const;

    // Byte count of the JPEG frame (0 if no frame).
    size_t getSize() const;

    // Release the PSRAM frame buffer back to the camera driver.
    // MUST be called after the JPEG has been sent over WebSocket.
    void release();

    // True if a frame is currently held (capture() succeeded, release() not yet called).
    bool hasFrame() const;

private:
    void* _fb = nullptr;    // opaque pointer to camera_fb_t to avoid header pollution
};
