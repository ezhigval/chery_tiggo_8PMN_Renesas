# Chery Emulator – High-Level Design

## Goal

Create a macOS application that emulates the Chery Tiggo 8 Pro Max head unit (Android + QNX stack) as realistically as possible:
- Full boot sequence from splash screen.
- Two displays: main HU (touch) and instrument cluster (non-touch).
- Realistic ignition/ACC/engine state machine.
- System should not "know" it is running inside an emulator.

## Stack Overview

- **UI (macOS)**: Swift + SwiftUI
  - Native desktop app, optimized for macOS.
  - Renders two virtual displays and a control panel.
  - Talks to core service via HTTP/WebSocket.

- **Core Service**: Python
  - Orchestrates QEMU (or another low-level emulator) for Android/QNX images.
  - Controls power states (OFF/ACC/IGN/ENGINE_RUNNING).
  - Exposes API for UI to:
    - Start/stop/reset emulator.
    - Change ignition state.
    - Fetch display frames/streams for HU and cluster.
    - Inject input events (touch, steering wheel buttons, etc.).

- **Emulation Backend**: QEMU (preferred)
  - Runs Android and QNX images extracted from the real head unit.
  - Device tree and peripherals configured to match T18FL3 as closely as practical.
  - Two video outputs (or one + additional surface) mapped to HU and cluster.
  - UART devices emulated according to the documented device tree.

## Main UI Layout (SwiftUI)

- **Main Window**
  - **Left/Right Panel – Control Panel**
    - Tabs:
      - `Vehicle`: ignition, engine state, gear (optional), speed/RPM sliders.
      - `Cabin`: climate, interior lights (future integration).
      - `Steering Wheel`: NAV/VOICE/MEDIA/VOLUME/etc. buttons.
      - `Infotainment`: quick actions (open Navi, Media, layouts).
      - `System`: emulator controls and debug info.
  - **Center – Main HU Display**
    - Shows video output of HU.
    - Accepts click/touch events and forwards them to the core.
  - **Secondary – Cluster Display**
    - Shows video output of instrument cluster.
    - Render-only (no input events).

## Ignition State Machine

States:
- **OFF**
  - Both displays dark.
- **ACC** (first short press)
  - HU starts boot sequence (splash, Android start).
  - Cluster mostly off or minimal indication.
- **IGN_ON** (second short press)
  - Full electrical power.
  - Cluster wakes up, HU continues/finishes loading.
- **ENGINE_RUNNING** (long press from IGN_ON)
  - Engine considered running.
  - Cluster shows RPM/engine indicators.
- **ENGINE_STOP / SHUTDOWN** (press from ENGINE_RUNNING)
  - Engine stops.
  - Cluster powers down.
  - HU stays on for a while, then transitions to shutdown according to system behavior.

The core service will implement a finite state machine and map UI events (button presses, hold duration) to these states, then send appropriate signals to the emulator (power events, ACPI, or equivalent mechanism configured for T18FL3).

## Emulator Integration (QEMU Direction)

- **Images**
  - Uses extracted Android and QNX images documented in:
    - `Documentation/11_QNX/*`
    - `Documentation/12_T18FL3/T18FL3_KNOWLEDGE_BASE.md`
    - and related extraction/boot documents.

- **Device Tree and UART**
  - UART devices and other peripherals follow the analyses in:
    - `Documentation/11_QNX/DEVICE_TREE_UART_ANALYSIS.md`
    - `Documentation/11_QNX/QEMU_UART_INTEGRATION.md`
  - QEMU configuration aims to:
    - Expose UART ports with the same names/addresses expected by the system.
    - Provide virtual implementations behind them (for logging, CAN simulation, etc.).

- **Displays**
  - Configure QEMU to provide:
    - Two framebuffers or two GPU outputs.
    - Or 1 main display + a mechanism for cluster (e.g., QNX or Android surface routed to second output), according to what is possible with the existing images.
  - The Python core will:
    - Capture both outputs (e.g., via VNC or framebuffer reads).
    - Stream frames to SwiftUI for HU and cluster views.

## Communication Between UI and Core

- **Protocol**: HTTP + WebSocket (JSON messages)
  - HTTP for control actions (start/stop emulator, change state).
  - WebSocket for real-time updates and display frames (or URLs to MJPEG/WebRTC streams if needed).

- **Key API concepts**
  - `/api/state` – get overall emulator and ignition state.
  - `/api/ignition` – POST with actions: `press_short`, `press_long`, `set_state`.
  - `/api/emulator` – start/stop/restart.
  - `/api/input/touch` – send touch events for HU display.
  - `/ws/hu` – stream HU display frames.
  - `/ws/cluster` – stream cluster display frames.

## Next Steps

1. Refine hardware emulation requirements based on:
   - `T18FL3_KNOWLEDGE_BASE.md` (resolutions, SoC details).
   - QNX/Android extraction and boot documents under `11_QNX`.
2. Define concrete QEMU command lines and configuration for dual displays and UART emulation.
3. Define detailed API schema (request/response JSON) between SwiftUI app and Python core.
4. Scaffold the SwiftUI app in `Development/Chery_Emulator` and the Python core service as a separate module.

> **Note:** This document must be kept in sync with discoveries from the real HU. When new details about hardware, UART, or boot flow appear in `Documentation/11_QNX` or `Documentation/12_T18FL3`, update this design accordingly.

---

## Implementation Notes (Cursor Environment)

- Due to environment constraints, the initial interactive UI is implemented as a **web interface** served by the Python core under `/ui`:
  - Location: `Development/Chery_Emulator/web/index.html`.
  - Purpose: Provide immediate control over ignition state and emulator lifecycle fully inside this repo.
- A future native macOS SwiftUI app remains a design option, but all concrete work here is done via the Python core + web UI to stay fully executable inside Cursor.

## Emulator configuration

- Runtime configuration for images and partitions is stored in:
  - `Development/Chery_Emulator/emulator_config.yaml`
- It currently tracks:
  - Android OTA zip and boot/system/vendor partition names.
  - QNX OTA zip and boot/system partition names.
- The Python core loads this via `EmulatorConfig.load_default()` in `core/emulator.py`.
- On `/emulator/start` the core validates that the configured OTA files exist under `firmware/`:
  - If files are missing → `emulator_status = ERROR` with a descriptive message.
  - If files are present → status moves to `RUNNING` (QEMU launch to be implemented).

## Ignition-driven emulator lifecycle

- The Python core automatically starts the emulator when ignition first leaves `OFF`:
  - Transition `OFF -> ACC` or `OFF -> ENGINE_RUNNING` triggers `emulator_manager.start()`.
  - This models the real behaviour where the HU starts booting as soon as ACC is enabled.
- Automatic shutdown based on ignition state (ACC/OFF timing, delayed HU power-down) is planned but **not yet implemented**:
  - For now the emulator keeps running until `/emulator/stop` is called explicitly.
  - Later revisions will add timers and state-based shutdown to better mimic real behaviour.

## QEMU command construction

- QEMU command is built by `EmulatorManager.build_qemu_command()` in `core/emulator.py`.
- It uses values from `Development/Chery_Emulator/emulator_config.yaml`:
  - `android.boot_img`, `android.system_img`, `android.vendor_img`, `android.product_img`.
  - Optional QNX images (`qnx_boot_img`, `qnx_system_img`) are reserved for future use.
- Current baseline command:
  - Machine: `virt,highmem=on`
  - CPU: `cortex-a57`
  - RAM: `4096 MB`, SMP: `4`
  - Disks: raw ext2 images attached via virtio-blk (`system`, `vendor`, `product`).
  - GPU: `virtio-gpu-pci`.
  - Network: user mode with `hostfwd=tcp::5555-:5555` for ADB.
  - Kernel params derived from real bootargs: `console=ttyAMA0,115200 androidboot.selinux=permissive androidboot.hardware=g6sh ...`.
- On `/emulator/start`:
  - Config is validated (presence of required Android images).
  - If valid → QEMU command string is built and written to `Development/Chery_Emulator/logs/qemu_command.txt`.
  - For now QEMU is **not** spawned from within the core; only the command is prepared and recorded.
  - If invalid → `emulator_status = ERROR` and `emulator_error` describes the missing image.

## Controls API

- Vehicle / cabin / steering wheel / infotainment controls are exposed via `/controls/*` endpoints:
  - `GET /controls/state` – returns last commands and history (for debugging and automation).
  - `POST /controls/vehicle` with `{ "command": "ACC" | "ENGINE_START" | "ENGINE_STOP" }`.
  - `POST /controls/cabin` with `{ "command": "CLIMATE_AUTO" | "CLIMATE_SYNC" | "REAR_DEFROST" }`.
  - `POST /controls/steering` with `{ "command": "NAV" | "MEDIA" | "VOICE" | "VOL_UP" | "VOL_DOWN" }`.
  - `POST /controls/infotainment` with `{ "command": "OPEN_NAV" | "OPEN_MEDIA" | "SPLIT_SCREEN" }`.
- Implementation lives in `core/controls.py` and `core/api_controls.py`:
  - All commands are recorded with timestamps in an in-memory history (up to 100 events).
  - This history can be used later to drive CAN/QNX/Android integration.
