#pragma once

// ============================================================================
// Synchora-Cam — Device Configuration
// ============================================================================

// Hardcoded identity token — server uses this to identify the CAM WebSocket
#define CAM_DEVICE_ID "synchora-cam"

// ============================================================================
// Camera Capture Settings
// ============================================================================

// Number of frames to discard before actual capture
// Allows OV2640 auto-exposure and white-balance to stabilise
#define WARMUP_FRAMES 3

// JPEG quality (0 = highest quality / largest file, 63 = lowest / smallest)
// 12 gives ~30–60 KB at SVGA — good Gemini accuracy, fast WiFi transmission
#define JPEG_QUALITY  12

// ============================================================================
// Capture Timing
// ============================================================================

// Flash pulse duration in milliseconds
#define FLASH_PULSE_MS 120
