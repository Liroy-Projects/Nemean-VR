# Nemean VR - Lion-Themed Mandalorian VR Helmet

## Project Overview
Nemean VR is a custom tactical VR helmet project inspired by Mandalorian armor and lion aesthetics. It integrates a Raspberry Pi 5 (8GB) to power a high-refresh, low-latency HUD (Head-Up Display) with optical VR lenses, USB camera passthrough, smart thermal cooling, and telemetry readouts.

The goal of this project is to build an immersive, functional sci-fi helmet shell with internal custom CAD mountings, optimized airflow, and integrated electronics for real-time vision processing.


## CAD & Hardware Design Files
* `mandalorian_helmet_base.stl`: Base outer helmet shell geometry used as the foundation for CAD remixing and internal bracket integration.
* **Planned CAD Modifications:** Custom internal mounts for the 5" HUD display, Raspberry Pi 5 bracket, Noctua PWM airflow ducting, and the integrated rear Li-Ion battery compartment with rear USB-C charging port.

---

## Bill of Materials (BOM)

| Component | Description | Quantity | Estimated Price | Purchase Link |
| :--- | :--- | :---: | :---: | :--- |
| **Raspberry Pi 5 (8GB)** | Main computing unit for HUD & vision processing | 1 | ~90 € | [BerryBase](https://www.berrybase.de) |
| **5" HD Display + VR Lenses** | Internal optical HUD assembly | 1 | ~45 € | [Amazon](https://www.amazon.de) |
| **USB 3.0 Wide-Angle Camera** | Low-latency passthrough camera | 1 | ~20 € | [Amazon](https://www.amazon.de) |
| **Noctua NF-A4x10 5V PWM** | Active thermal management fan | 1 | ~15 € | [Amazon](https://www.amazon.de) |
| **Integrated Li-Ion Power Kit** | Li-Ion cells + BMS/Boost charging board with rear USB-C port | 1 | ~18 € | [Amazon](https://www.amazon.de) |

---

## System Wiring & Hardware Architecture

```text
[ Rear USB-C Port ] ---> [ BMS / Charge Board ] ---> [ Li-Ion Battery Pack ]
                                                               |
                                                       (5V Power Delivery)
                                                               v
[ USB Camera ] ---------> (USB 3.0) -------------> [ Raspberry Pi 5 ] ---> (HDMI) ---> [ 5" HUD Display ]
                                                               |
                                                         (GPIO PWM 5V)
                                                               v
                                                     [ Noctua Cooling Fan ]
