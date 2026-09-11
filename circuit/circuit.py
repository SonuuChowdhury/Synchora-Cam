#!/usr/bin/env python3
"""
Generate the ESP32-CAM (AI-Thinker) Flashing & Circuit Schematic as SVG and HTML.

================================================================================
 READ THIS FIRST — instructions for future AI agents / developers
================================================================================

WHAT THIS IS:
  This script generates the professional wiring diagram for flashing the
  AI-Thinker ESP32-CAM using an Arduino UNO (CH340) as a USB-to-UART bridge.
  It generates both:
    1. circuit_diagram.svg
    2. circuit.html (interactive dark-mode viewer with zoom/pan)

KEY CIRCUIT HIGHLIGHTS:
  1. Arduino UNO in RESET Mode:
     - RESET tied to GND halts the ATmega328P, enabling pure USB-UART bridge mode.
     - Uno RX (D0) is the USB Bridge TX output -> feeds ESP32-CAM U0R (RX).
     - Uno TX (D1) is the USB Bridge RX input  <- receives from ESP32-CAM U0T (TX).

  2. 5V -> 3.3V Logic Level Shifter (Voltage Divider):
     - R1 = 1kΩ in series from Uno RX (D0).
     - R2 = 2kΩ pull-down to GND.
     - V_out = 5V * (2k / (1k + 2k)) = 3.33V (Safe for ESP32 3.3V GPIO).

  3. Direct TX Return Line:
     - ESP32-CAM U0T (3.3V) -> Uno TX (D1) direct line (3.3V is well above the 5V TTL HIGH threshold ~3.0V).

  4. Bootloader Mode:
     - GPIO 0 connected to GND during flashing; disconnected for normal runtime.

================================================================================
"""

import os

# ---------------------------------------------------------------- palette
BG          = "#0b1220"
BG_GRID     = "#141d31"
PANEL       = "#111a2e"
PANEL_EDGE  = "#2a3a5c"
BOX_FILL    = "#0f172a"
BOX_SUB     = "#1e293b"
TEXT_MAIN   = "#e8edf9"
TEXT_DIM    = "#7f8cab"
TEXT_LABEL  = "#a9b6d6"

# Power & Ground Colors
C_5V        = "#f87171"   # 5V Power Bus (Red)
C_33V       = "#fb923c"   # 3.3V Power Bus (Orange)
C_GND       = "#6b7280"   # Common Ground (Gray)

# Signal Colors
C_UART_TX   = "#38bdf8"   # USB TX / ESP RX (Sky Blue)
C_UART_RX   = "#f472b6"   # ESP TX / USB RX (Pink)
C_BOOT      = "#fbbf24"   # Boot Mode GPIO 0 (Amber Gold)
C_RST       = "#a78bfa"   # Uno Reset Hold (Violet)
C_FLASH     = "#facc15"   # Flash LED (Yellow)
C_CAM       = "#22d3ee"   # Camera Sensor Bus (Cyan)
C_STATUS    = "#f43f5e"   # Status Indicator (Rose Red)

CPIN        = "#94a3b8"
FONT        = "'JetBrains Mono','Fira Code','Courier New',monospace"

W, H = 2000, 1180
BUS_5V  = 70
BUS_BOT = 960

svg = []
def add(s): svg.append(s)

def text(x, y, s, size=15, color=TEXT_MAIN, anchor="start", weight="400", family=FONT, style=""):
    s_escaped = str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    add(f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" '
        f'fill="{color}" text-anchor="{anchor}" font-weight="{weight}" style="{style}">{s_escaped}</text>')

def hline(x1, x2, y, color, width=2.4, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    add(f'<line x1="{min(x1,x2)}" y1="{y}" x2="{max(x1,x2)}" y2="{y}" stroke="{color}" '
        f'stroke-width="{width}" stroke-linecap="round"{d}/>')

def vline(x, y1, y2, color, width=2.4, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    add(f'<line x1="{x}" y1="{min(y1,y2)}" x2="{x}" y2="{max(y1,y2)}" stroke="{color}" '
        f'stroke-width="{width}" stroke-linecap="round"{d}/>')

def line(x1, y1, x2, y2, color, width=2.4, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    add(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" '
        f'stroke-width="{width}" stroke-linecap="round"{d}/>')

def dot(x, y, color, r=4.5):
    """Junction / solder dot at wire connections."""
    add(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}"/>')

def resistor_h(cx, cy, w=70, h=20, color=TEXT_MAIN, label="1kΩ"):
    """Horizontal box resistor symbol."""
    rx, ry = cx - w/2, cy - h/2
    add(f'<rect x="{rx}" y="{ry}" width="{w}" height="{h}" rx="3" fill="{BOX_SUB}" stroke="{color}" stroke-width="1.8"/>')
    if label:
        text(cx, ry - 8, label, 12, TEXT_LABEL, "middle", "700")
    return rx, rx + w

def resistor_v(cx, cy, w=20, h=70, color=TEXT_MAIN, label="2kΩ"):
    """Vertical box resistor symbol."""
    rx, ry = cx - w/2, cy - h/2
    add(f'<rect x="{rx}" y="{ry}" width="{w}" height="{h}" rx="3" fill="{BOX_SUB}" stroke="{color}" stroke-width="1.8"/>')
    if label:
        text(rx + w + 10, cy + 4, label, 12, TEXT_LABEL, "start", "700")
    return ry, ry + h

def module_box(x, y, w, h, title, subtitle, accent=C_CAM, title_y_off=24):
    """Draw stylized card container with drop shadow, border, and top accent bar."""
    add(f'<rect x="{x+3}" y="{y+3}" width="{w}" height="{h}" rx="8" fill="#000" opacity="0.45"/>')
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{BOX_FILL}" stroke="{PANEL_EDGE}" stroke-width="1.6"/>')
    add(f'<rect x="{x}" y="{y}" width="{w}" height="4" rx="2" fill="{accent}"/>')
    text(x + w/2, y + title_y_off, title, 16, TEXT_MAIN, "middle", "700")
    if subtitle:
        text(x + w/2, y + title_y_off + 18, subtitle, 12, TEXT_DIM, "middle")

def generate_svg():
    global svg
    svg = []

    add(f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" font-family="{FONT}">')

    # Background & grid
    add(f'<rect width="{W}" height="{H}" fill="{BG}"/>')
    add('<defs>')
    add(f'<pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse">'
        f'<path d="M 32 0 L 0 0 0 32" fill="none" stroke="{BG_GRID}" stroke-width="1"/></pattern>')
    add('</defs>')
    add(f'<rect width="{W}" height="{H}" fill="url(#grid)"/>')

    # Title header
    text(W/2, 34, "SYNCHORA-CAM — FLASHING & HARDWARE SCHEMATIC", 22, TEXT_MAIN, "middle", "700")
    text(W/2, 52, "Arduino UNO (CH340) USB-UART Bridge • 5V → 3.3V Logic Level Shifting • AI-Thinker ESP32-CAM (OV2640)", 12, TEXT_DIM, "middle")

    # Buses
    # 5V Power Rail
    hline(60, W-60, BUS_5V, C_5V, 3.5)
    text(70, BUS_5V-7, "5V POWER BUS (USB VBUS)", 13, C_5V, "start", "700")

    # GND Rail
    hline(60, W-60, BUS_BOT, C_GND, 3.5)
    text(70, BUS_BOT+24, "COMMON GND BUS (GROUND RAIL)", 13, C_GND, "start", "700")

    # =========================================================================
    # CARD 1: ARDUINO UNO (CH340 USB-UART BRIDGE)
    # =========================================================================
    u_x, u_y, u_w, u_h = 80, 140, 420, 760
    module_box(u_x, u_y, u_w, u_h, "REES52 / ARDUINO UNO", "USB-to-UART Programmer Bridge (CH340)", C_UART_TX)

    # Sub-badge explaining ATmega reset state
    add(f'<rect x="{u_x + 20}" y="{u_y + 65}" width="{u_w - 40}" height="55" rx="6" fill="{BOX_SUB}" stroke="{C_RST}" stroke-width="1.2"/>')
    text(u_x + u_w/2, u_y + 88, "ATmega328P MCU State: HALTED", 12.5, C_RST, "middle", "700")
    text(u_x + u_w/2, u_y + 107, "RESET connected to GND bypasses onboard MCU", 10.5, TEXT_LABEL, "middle")

    # Uno Pin Y-levels
    u_p_5v   = 240
    u_p_rx   = 380  # RX (D0) -> USB TX
    u_p_tx   = 560  # TX (D1) -> USB RX
    u_p_rst  = 720  # RESET pin
    u_p_gnd  = 840  # GND pin

    # Pin Outlines & Labels on Uno right border
    uno_pins = [
        ("5V (Power Out)", u_p_5v, C_5V, "Direct 5V supply to ESP32-CAM"),
        ("RX (D0) [USB TXD]", u_p_rx, C_UART_TX, "CH340 Transmit Output (5V TTL)"),
        ("TX (D1) [USB RXD]", u_p_tx, C_UART_RX, "CH340 Receive Input (5V TTL tolerant)"),
        ("RESET", u_p_rst, C_RST, "Jumpered to GND"),
        ("GND", u_p_gnd, C_GND, "Common Ground"),
    ]

    for lbl, py, col, desc in uno_pins:
        dot(u_x + u_w, py, col, 4)
        text(u_x + u_w - 16, py - 8, lbl, 13, col, "end", "700")
        text(u_x + u_w - 16, py + 16, desc, 10, TEXT_DIM, "end")

    # 1. Uno 5V to 5V Rail
    vline(u_x + u_w + 30, BUS_5V, u_p_5v, C_5V, 2.6)
    hline(u_x + u_w, u_x + u_w + 30, u_p_5v, C_5V, 2.6)
    dot(u_x + u_w + 30, BUS_5V, C_5V, 4.5)

    # 2. Uno GND to GND Rail
    vline(u_x + u_w + 30, u_p_gnd, BUS_BOT, C_GND, 2.6)
    hline(u_x + u_w, u_x + u_w + 30, u_p_gnd, C_GND, 2.6)
    dot(u_x + u_w + 30, BUS_BOT, C_GND, 4.5)

    # 3. Uno RESET Jumper to GND
    hline(u_x + u_w, u_x + u_w + 60, u_p_rst, C_RST, 2.6)
    vline(u_x + u_w + 60, u_p_rst, BUS_BOT, C_RST, 2.6)
    dot(u_x + u_w + 60, BUS_BOT, C_RST, 4.5)
    add(f'<rect x="{u_x + u_w + 75}" y="{u_p_rst - 18}" width="200" height="36" rx="4" fill="{BOX_SUB}" stroke="{C_RST}" stroke-width="1.2"/>')
    text(u_x + u_w + 85, u_p_rst + 4, "RESET → GND JUMPER", 11, C_RST, "start", "700")

    # =========================================================================
    # CARD 2: ESP32-CAM AI-THINKER
    # =========================================================================
    e_x, e_y, e_w, e_h = 1380, 140, 540, 760
    module_box(e_x, e_y, e_w, e_h, "ESP32-CAM (AI-THINKER)", "ESP32-S • OV2640 Camera • 4MB PSRAM", C_CAM)

    # ESP32-CAM Left Pin Y-levels
    e_p_5v   = 240
    e_p_rx   = 380  # U0R (RX)
    e_p_tx   = 560  # U0T (TX)
    e_p_boot = 720  # GPIO 0
    e_p_gnd  = 840  # GND

    esp_pins = [
        ("5V (VCC in)", e_p_5v, C_5V, "Onboard AMS1117-3.3 regulator input"),
        ("U0R (RX)", e_p_rx, C_UART_TX, "UART0 RX (3.3V Logic Level)"),
        ("U0T (TX)", e_p_tx, C_UART_RX, "UART0 TX (3.3V Logic Level)"),
        ("GPIO 0", e_p_boot, C_BOOT, "Boot Mode selection pin"),
        ("GND", e_p_gnd, C_GND, "Common Ground"),
    ]

    for lbl, py, col, desc in esp_pins:
        dot(e_x, py, col, 4)
        text(e_x + 16, py - 8, lbl, 13, col, "start", "700")
        text(e_x + 16, py + 16, desc, 10, TEXT_DIM, "start")

    # 1. ESP32 5V to 5V Rail
    vline(e_x - 30, BUS_5V, e_p_5v, C_5V, 2.6)
    hline(e_x - 30, e_x, e_p_5v, C_5V, 2.6)
    dot(e_x - 30, BUS_5V, C_5V, 4.5)

    # 2. ESP32 GND to GND Rail
    vline(e_x - 30, e_p_gnd, BUS_BOT, C_GND, 2.6)
    hline(e_x - 30, e_x, e_p_gnd, C_GND, 2.6)
    dot(e_x - 30, BUS_BOT, C_GND, 4.5)

    # 3. ESP32 GPIO 0 Boot Jumper to GND
    hline(e_x - 60, e_x, e_p_boot, C_BOOT, 2.6)
    vline(e_x - 60, e_p_boot, BUS_BOT, C_BOOT, 2.6)
    dot(e_x - 60, BUS_BOT, C_BOOT, 4.5)
    add(f'<rect x="{e_x - 310}" y="{e_p_boot - 26}" width="235" height="52" rx="6" fill="{BOX_SUB}" stroke="{C_BOOT}" stroke-width="1.2"/>')
    text(e_x - 300, e_p_boot - 6, "GPIO 0 → GND JUMPER", 11.5, C_BOOT, "start", "700")
    text(e_x - 300, e_p_boot + 14, "Bridge for Flash, Remove to RUN", 10, TEXT_LABEL, "start")

    # Internal Modules inside ESP32-CAM box
    # OV2640 Sub-card
    cam_box_x = e_x + 220
    add(f'<rect x="{cam_box_x}" y="{e_y + 70}" width="290" height="230" rx="6" fill="{BOX_SUB}" stroke="{PANEL_EDGE}" stroke-width="1.2"/>')
    add(f'<rect x="{cam_box_x}" y="{e_y + 70}" width="290" height="3" rx="1" fill="{C_CAM}"/>')
    text(cam_box_x + 145, e_y + 95, "OV2640 Camera Module", 13.5, TEXT_MAIN, "middle", "700")
    text(cam_box_x + 145, e_y + 115, "2.0 MP • UXGA / SVGA JPEG", 11, C_CAM, "middle")

    cam_specs = [
        "Internal SCCB (SIOD:26, SIOC:27)",
        "Sync: VSYNC:25, HREF:23, PCLK:22",
        "Data: D0..D7 (GPIO 5,18,19,21,36..35)",
        "Clock: XCLK:0 (20MHz)",
        "Memory: 4MB External PSRAM Enabled",
    ]
    for i, spec in enumerate(cam_specs):
        text(cam_box_x + 16, e_y + 145 + i * 20, "• " + spec, 10, TEXT_LABEL, "start")

    # Flash LED Sub-card
    add(f'<rect x="{cam_box_x}" y="{e_y + 320}" width="290" height="100" rx="6" fill="{BOX_SUB}" stroke="{PANEL_EDGE}" stroke-width="1.2"/>')
    add(f'<rect x="{cam_box_x}" y="{e_y + 320}" width="290" height="3" rx="1" fill="{C_FLASH}"/>')
    text(cam_box_x + 145, e_y + 345, "High-Power Flash LED", 13, TEXT_MAIN, "middle", "700")
    text(cam_box_x + 145, e_y + 365, "GPIO 4 • Active HIGH (120ms Pulse)", 11, C_FLASH, "middle")
    text(cam_box_x + 145, e_y + 395, "Illuminates scene during capture", 10, TEXT_DIM, "middle")

    # Status LED Sub-card
    add(f'<rect x="{cam_box_x}" y="{e_y + 440}" width="290" height="110" rx="6" fill="{BOX_SUB}" stroke="{PANEL_EDGE}" stroke-width="1.2"/>')
    add(f'<rect x="{cam_box_x}" y="{e_y + 440}" width="290" height="3" rx="1" fill="{C_STATUS}"/>')
    text(cam_box_x + 145, e_y + 465, "Status Indicator LED", 13, TEXT_MAIN, "middle", "700")
    text(cam_box_x + 145, e_y + 485, "GPIO 33 • Active LOW (Red LED)", 11, C_STATUS, "middle")
    text(cam_box_x + 145, e_y + 512, "Fast: WiFi Sync | Slow: WS Sync", 10, TEXT_LABEL, "middle")
    text(cam_box_x + 145, e_y + 530, "Solid ON: Fully Online", 10, C_UART_TX, "middle", "700")

    # =========================================================================
    # MIDDLE ROUTING & LEVEL SHIFTER
    # =========================================================================

    # -------------------------------------------------------------------------
    # SIGNAL 1: Uno RX (D0) -> 1k/2k Divider -> ESP32-CAM U0R (RX)
    # -------------------------------------------------------------------------
    r1_cx = 760
    div_junction_x = 900
    r2_cy = 480

    # Uno RX(D0) wire to R1
    hline(u_x + u_w, r1_cx - 35, u_p_rx, C_UART_TX, 2.6)

    # Resistor R1 (1kΩ in series)
    resistor_h(r1_cx, u_p_rx, 70, 22, C_UART_TX, "R1 = 1kΩ")

    # R1 to Divider Junction
    hline(r1_cx + 35, div_junction_x, u_p_rx, C_UART_TX, 2.6)
    dot(div_junction_x, u_p_rx, C_UART_TX, 5)

    # Divider Junction down through R2 (2kΩ) to GND
    vline(div_junction_x, u_p_rx, r2_cy - 35, C_GND, 2.4)
    resistor_v(div_junction_x, r2_cy, 22, 70, C_GND, "R2 = 2kΩ")
    vline(div_junction_x, r2_cy + 35, BUS_BOT, C_GND, 2.4)
    dot(div_junction_x, BUS_BOT, C_GND, 4.5)

    # Divider Junction forward to ESP32 U0R (RX)
    hline(div_junction_x, e_x, u_p_rx, C_UART_TX, 2.6)

    # Formula Callout Badge for Level Shifter
    add(f'<rect x="680" y="280" width="440" height="68" rx="6" fill="{BOX_SUB}" stroke="{C_UART_TX}" stroke-width="1.2"/>')
    text(900, 304, "5V → 3.3V LOGIC LEVEL SHIFTER (VOLTAGE DIVIDER)", 11.5, C_UART_TX, "middle", "700")
    text(900, 324, "V_out = 5.0V × [2kΩ / (1kΩ + 2kΩ)] = 3.33V (Safe for ESP32)", 11, TEXT_MAIN, "middle")
    text(900, 339, "Protects ESP32 3.3V GPIO against 5V over-voltage damage", 9.5, TEXT_DIM, "middle")

    # -------------------------------------------------------------------------
    # SIGNAL 2: ESP32-CAM U0T (TX) -> Uno TX (D1) (Direct line)
    # -------------------------------------------------------------------------
    hline(u_x + u_w, e_x, u_p_tx, C_UART_RX, 2.6)

    # TX Return Annotation Badge
    add(f'<rect x="680" y="585" width="440" height="52" rx="6" fill="{BOX_SUB}" stroke="{C_UART_RX}" stroke-width="1.2"/>')
    text(900, 608, "DIRECT TX RETURN (3.3V → 5V TTL COMPATIBLE)", 11.5, C_UART_RX, "middle", "700")
    text(900, 626, "ESP32 3.3V HIGH is well above Uno CH340 input threshold (~2.7V)", 10.5, TEXT_LABEL, "middle")

    # =========================================================================
    # BOTTOM LEGEND & FLASHING INSTRUCTIONS PANEL
    # =========================================================================
    lx, ly, lw, lh = 80, 995, W - 160, 160
    add(f'<rect x="{lx+3}" y="{ly+3}" width="{lw}" height="{lh}" rx="10" fill="#000" opacity="0.45"/>')
    add(f'<rect x="{lx}" y="{ly}" width="{lw}" height="{lh}" rx="10" fill="{PANEL}" stroke="{PANEL_EDGE}" stroke-width="1.4"/>')
    text(lx + 24, ly + 28, "SCHEMATIC LEGEND & STEP-BY-STEP UPLOAD PROCEDURE", 14, TEXT_MAIN, "start", "700")

    # Col 1: Wire color legend
    leg1 = [
        (C_5V,      "5V VBUS Rail (Direct from USB)"),
        (C_GND,     "Common Ground (GND)"),
        (C_UART_TX, "Uno RX(D0) → 3.33V Shifted → ESP32 U0R"),
        (C_UART_RX, "ESP32 U0T (3.3V) → Uno TX(D1) Direct"),
    ]
    # Col 2: Jumper states
    leg2 = [
        (C_RST,     "Uno RESET → GND (Halts ATmega MCU)"),
        (C_BOOT,    "ESP32 GPIO0 → GND (Bootloader Mode)"),
        (C_FLASH,   "Flash LED: GPIO 4 (Active HIGH)"),
        (C_STATUS,  "Status LED: GPIO 33 (Active LOW)"),
    ]
    # Col 3: Upload Procedure
    steps = [
        "1. Bridge Uno RESET to GND and ESP32 GPIO 0 to GND.",
        "2. Connect USB cable, press ESP32 RST button once.",
        "3. Run PlatformIO Upload (COM port detected by CH340).",
        "4. When finished, REMOVE GPIO 0 jumper and press RST.",
    ]

    # Render Col 1
    c1_x = lx + 24
    for i, (col, lbl) in enumerate(leg1):
        cyy = ly + 52 + i * 24
        hline(c1_x, c1_x + 24, cyy, col, 3)
        dot(c1_x + 24, cyy, col, 3)
        text(c1_x + 34, cyy + 4, lbl, 11, TEXT_LABEL, "start")

    # Render Col 2
    c2_x = lx + 490
    for i, (col, lbl) in enumerate(leg2):
        cyy = ly + 52 + i * 24
        hline(c2_x, c2_x + 24, cyy, col, 3)
        dot(c2_x + 24, cyy, col, 3)
        text(c2_x + 34, cyy + 4, lbl, 11, TEXT_LABEL, "start")

    # Render Col 3 (Steps box)
    c3_x = lx + 970
    add(f'<rect x="{c3_x}" y="{ly + 40}" width="{lw - 1000}" height="104" rx="6" fill="{BOX_SUB}" stroke="{PANEL_EDGE}" stroke-width="1.2"/>')
    text(c3_x + 16, ly + 60, "PROGRAMMING SEQUENCE:", 11, C_UART_TX, "start", "700")
    for i, step in enumerate(steps):
        text(c3_x + 16, ly + 80 + i * 16, step, 10.5, TEXT_MAIN, "start")

    add('</svg>')
    return "\n".join(svg)

def generate_html(svg_content):
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Synchora-Cam Circuit & Flashing Schematic</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Outfit:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg: #070d18;
            --panel: #0d1527;
            --panel-border: #1e293b;
            --text-main: #f1f5f9;
            --text-dim: #94a3b8;
            --accent-blue: #38bdf8;
            --accent-pink: #f472b6;
            --accent-green: #10b981;
            --accent-amber: #fbbf24;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            background: var(--bg);
            color: var(--text-main);
            font-family: 'Outfit', sans-serif;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 2rem 1rem;
        }}

        header {{
            text-align: center;
            margin-bottom: 1.5rem;
        }}

        h1 {{
            font-size: 2rem;
            font-weight: 700;
            background: linear-gradient(135deg, #38bdf8 0%, #818cf8 50%, #f472b6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }}

        p.subtitle {{
            color: var(--text-dim);
            font-size: 0.95rem;
        }}

        .diagram-container {{
            width: 100%;
            max-width: 1400px;
            background: var(--panel);
            border: 1px solid var(--panel-border);
            border-radius: 12px;
            padding: 1rem;
            box-shadow: 0 20px 40px rgba(0,0,0,0.5);
            overflow-x: auto;
        }}

        .diagram-container svg {{
            width: 100%;
            height: auto;
            min-width: 900px;
            display: block;
        }}

        .specs-grid {{
            width: 100%;
            max-width: 1400px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 1.25rem;
            margin-top: 1.5rem;
        }}

        .card {{
            background: var(--panel);
            border: 1px solid var(--panel-border);
            border-radius: 10px;
            padding: 1.25rem;
        }}

        .card h2 {{
            font-size: 1.1rem;
            margin-bottom: 0.75rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .card ul {{
            list-style: none;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.85rem;
            color: var(--text-dim);
            line-height: 1.7;
        }}

        .card ul li strong {{
            color: var(--text-main);
        }}

        .tag {{
            display: inline-block;
            padding: 0.15rem 0.5rem;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 700;
        }}
        .tag-blue {{ background: rgba(56, 189, 248, 0.15); color: #38bdf8; }}
        .tag-amber {{ background: rgba(251, 191, 36, 0.15); color: #fbbf24; }}
        .tag-green {{ background: rgba(16, 185, 129, 0.15); color: #10b981; }}
    </style>
</head>
<body>
    <header>
        <h1>Synchora-Cam Flashing & Wiring</h1>
        <p class="subtitle">AI-Thinker ESP32-CAM (OV2640) + Arduino UNO (CH340) USB-to-UART Bridge with 5V to 3.3V Level Shifting</p>
    </header>

    <div class="diagram-container">
        {svg_content}
    </div>

    <div class="specs-grid">
        <div class="card">
            <h2><span class="tag tag-blue">UART PIN MAP</span> Connection Table</h2>
            <ul>
                <li><strong>Uno 5V:</strong> ➔ ESP32-CAM 5V (VCC in)</li>
                <li><strong>Uno GND:</strong> ➔ ESP32-CAM GND</li>
                <li><strong>Uno RESET:</strong> ➔ Uno GND (holds ATmega halted)</li>
                <li><strong>Uno RX (D0):</strong> ➔ 1kΩ / 2kΩ Divider ➔ ESP32-CAM U0R</li>
                <li><strong>Uno TX (D1):</strong> ➔ ESP32-CAM U0T (Direct line)</li>
                <li><strong>ESP32 GPIO 0:</strong> ➔ GND (during flashing only)</li>
            </ul>
        </div>

        <div class="card">
            <h2><span class="tag tag-amber">SAFETY</span> Level Shifter Specs</h2>
            <ul>
                <li><strong>R1 (Series):</strong> 1kΩ (1/4W metal or carbon film)</li>
                <li><strong>R2 (Pull-down):</strong> 2kΩ (to Common GND)</li>
                <li><strong>Output Voltage:</strong> 5.0V × 2/3 = 3.33V</li>
                <li><strong>Protection:</strong> Prevents 5V UART signals from burning out ESP32 3.3V IO gates.</li>
            </ul>
        </div>

        <div class="card">
            <h2><span class="tag tag-green">FLASH PROTOCOL</span> Step-by-Step</h2>
            <ul>
                <li><strong>1.</strong> Wire circuit and bridge GPIO0 to GND.</li>
                <li><strong>2.</strong> Connect USB & press ESP32-CAM RST button.</li>
                <li><strong>3.</strong> Flash with: <code style="color:#38bdf8">pio run -t upload</code></li>
                <li><strong>4.</strong> Disconnect GPIO0 from GND and press RST.</li>
                <li><strong>5.</strong> Status LED glows solid when connected!</li>
            </ul>
        </div>
    </div>
</body>
</html>
"""
    return html

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    svg_content = generate_svg()
    
    svg_path = os.path.join(base_dir, "circuit_diagram.svg")
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print(f"[OK] Saved SVG to {svg_path}")

    html_content = generate_html(svg_content)
    html_path = os.path.join(base_dir, "circuit.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"[OK] Saved HTML to {html_path}")

if __name__ == "__main__":
    main()
