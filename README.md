# Nemean VR - Lion-Themed Mandalorian VR Helmet

## Project Overview
Nemean VR is a custom tactical VR helmet project inspired by Mandalorian armor and lion aesthetics. It integrates a Raspberry Pi 5 (8GB) to power a high-refresh, low-latency HUD (Head-Up Display) with optical VR lenses, USB camera passthrough, smart thermal cooling, and telemetry readouts.

The goal of this project is to build an immersive, functional sci-fi helmet shell with internal custom CAD mountings, optimized airflow, and integrated electronics for real-time vision processing.

## Project Images & CAD Preview
![Nemean VR Concept & Preview](bambu_studio_preview.png)

## Bill of Materials (BOM)
| Component | Description | Quantity | Estimated Price | Purchase Link |
| :--- | :--- | :--- | :--- | :--- |
| **Raspberry Pi 5 (8GB)** | Main computing unit for HUD & vision processing | 1 | ~90 € | [BerryBase](https://www.berrybase.de) |
| **5" HD Display + VR Lenses** | Internal optical HUD assembly | 1 | ~45 € | [Amazon](https://www.amazon.de) |
| **USB 3.0 Wide-Angle Camera** | Low-latency passthrough camera | 1 | ~20 € | [Amazon](https://www.amazon.de) |
| **Noctua NF-A4x10 5V PWM** | Active thermal management fan | 1 | ~15 € | [Amazon](https://www.amazon.de) |
| **Custom Battery & USB-C Charge Module** | Integrated rear helmet UPS power & charging board | 1 | ~18 € | [BerryBase](https://www.berrybase.de) |

## System Wiring & Hardware Architecture
[ External USB-C Charger ] ---> [ Rear Helmet Charge Port ] ---> [ Internal Battery Pack (UPS) ]
                                                                       |
                                                                       v
[ USB Camera ] ---> (USB 3.0) ---> [ Raspberry Pi 5 ] ---------------> [ 5" HUD Display ]
                                            |
                                      (GPIO PWM 5V)
                                            v
                                   [ Noctua Cooling Fan ]

## CAD & Code Files
The CAD files (.STL / .3MF / .STEP) for internal lens brackets, rear battery compartment, Pi mounting braces, and helmet housing are pushed directly to this repository.
