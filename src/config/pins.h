#pragma once

// ============================================================================
// AI-Thinker ESP32-CAM — OV2640 Camera Pin Definitions
// ============================================================================

// Power & Clock
#define CAM_PIN_PWDN    32
#define CAM_PIN_RESET   -1   // Software reset only — not wired on AI-Thinker
#define CAM_PIN_XCLK     0

// SCCB (I2C-like camera control bus)
#define CAM_PIN_SIOD    26
#define CAM_PIN_SIOC    27

// Sync signals
#define CAM_PIN_VSYNC   25
#define CAM_PIN_HREF    23
#define CAM_PIN_PCLK    22

// Data bus D0–D7
#define CAM_PIN_D7      35
#define CAM_PIN_D6      34
#define CAM_PIN_D5      39
#define CAM_PIN_D4      36
#define CAM_PIN_D3      21
#define CAM_PIN_D2      19
#define CAM_PIN_D1      18
#define CAM_PIN_D0       5

// ============================================================================
// LED Pins
// ============================================================================

// High-power white flash LED — active HIGH, fires briefly on capture
#define FLASH_LED_PIN    4

// Small red status indicator — ACTIVE LOW (LOW = ON, HIGH = OFF)
#define STATUS_LED_PIN  33
