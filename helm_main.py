# -*- coding: utf-8 -*-
"""
helm_main.py — LiroyVR-Helm: alles zusammen
============================================

Kette:  Capture-Card (1) -> VR-Split+Linse (2) -> Liroy-HUD (3) -> Lüfter (4)

Start (am PC zum Testen, ohne Hardware):
    python helm_main.py --simulate

Start (am Pi mit Capture-Card und Lüfter):
    sudo python helm_main.py

Tasten im Fenster:
    h = HUD an/aus      v = VR-Modus an/aus (rohes Bild)
    d = Duplex/Seitenmodus umschalten (dup <-> half)
    q = beenden
"""

import argparse
import sys
import time
import threading

import numpy as np
import cv2

import helm_capture
import helm_vr_renderer
import helm_ui_overlay
import helm_hardware_control


class FanThread(threading.Thread):
    """Regelt den Lüfter im Hintergrund (Schritt 4), ohne den Bildloop zu blocken."""

    def __init__(self, simulate=False):
        super().__init__(daemon=True)
        self.simulate = simulate
        self.fan = helm_hardware_control.FanController(simulate=simulate)
        self.temp = None
        self.percent = 0
        self._stop = threading.Event()

    def run(self):
        while not self._stop.is_set():
            self.temp = helm_hardware_control.read_cpu_temp()
            self.percent, _ = helm_hardware_control.regulate_fan(self.fan, self.temp, self.percent)
            self._stop.wait(2.0)

    def stop(self):
        self._stop.set()
        self.join(timeout=3)
        self.fan.set_percent(0)
        self.fan.close()

    def hud_text(self):
        fan = "Luefter: %d%%" % self.percent
        if self.temp is not None:
            fan += " | CPU %.1fC" % self.temp
        return fan


def main():
    ap = argparse.ArgumentParser(description="LiroyVR-Helm — Nintendo Switch in VR mit Liroy-HUD")
    ap.add_argument("--device", type=int, default=0, help="Capture-Card-Index (Standard 0)")
    ap.add_argument("--simulate", action="store_true", help="Testsignal statt Capture-Card, Lüfter nur loggen")
    ap.add_argument("--mode", choices=["dup", "half"], default="dup",
                    help="dup: beide Augen sehen das ganze Bild | half: Switch-Seiten-modus")
    ap.add_argument("--no-vr", action="store_true", help="Nur Spielbild + HUD (ohne Split/Verzerrung)")
    ap.add_argument("--panel", type=int, default=720, help="Augen-Panel-Größe (Standard 720)")
    ap.add_argument("--k1", type=float, default=helm_vr_renderer.LENS_K1, help="Barrel-Stärke")
    args = ap.parse_args()

    print("=" * 60)
    print(" LiroyVR-Helm startet")
    print("=" * 60)

    # --- Schritt 1: Eingang ---
    cam = helm_capture.SwitchCapture(device=args.device,
                                     allow_test_signal=args.simulate)
    if args.simulate:
        cam.cap = None
        cam._running = True
        cam._thread = threading.Thread(target=cam._loop, daemon=True)
        cam._thread.start()
    else:
        cam.start()

    # --- Schritt 2: VR-Renderer ---
    renderer = helm_vr_renderer.VRRenderer(panel_w=args.panel, panel_h=args.panel, k1=args.k1)
    vr_on = not args.no_vr
    mode = args.mode

    # --- Schritt 3: HUD ---
    hud = helm_ui_overlay.LiroyHud()
    hud_on = True

    # --- Schritt 4: Lüfter im Hintergrund ---
    fan_thread = FanThread(simulate=args.simulate)
    fan_thread.start()

    print("Tasten: h=HUD, v=VR an/aus, d=Modus dup/half, q=Ende")
    win = "LiroyVR-Helm"
    cv2.namedWindow(win, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(win, 1280, 720)

    fps_hist = []
    try:
        while True:
            frame = cam.read()
            if frame is None:
                time.sleep(0.02)
                continue

            # Schritt 2: VR
            out = renderer.render(frame, mode=mode) if vr_on else frame.copy()

            # Schritt 3: HUD
            fps_hist.append(time.time())
            if len(fps_hist) > 30:
                fps_hist.pop(0)
            fps = 0.0
            if len(fps_hist) > 2:
                span = fps_hist[-1] - fps_hist[0]
                if span > 0:
                    fps = (len(fps_hist) - 1) / span

            hud.draw(out, extra={
                "fps": "%.0f" % fps,
                "quelle": cam.status()["quelle"],
                "fan": fan_thread.hud_text(),
                "hint": ("VR: %s/%s" % ("an" if vr_on else "aus", mode)) if hud_on else "",
            })

            cv2.imshow(win, out)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            elif key == ord("h"):
                hud_on = not hud_on
            elif key == ord("v"):
                vr_on = not vr_on
            elif key == ord("d"):
                mode = "half" if mode == "dup" else "dup"
    except KeyboardInterrupt:
        pass
    finally:
        cam.stop()
        fan_thread.stop()
        cv2.destroyAllWindows()
        print("Helm aus. Lüfter gestoppt, Kamera freigegeben.")


if __name__ == "__main__":
    main()
