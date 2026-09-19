# -*- coding: utf-8 -*-
"""
helm_capture.py — Schritt 1: Video-Eingang (Nintendo Switch -> Capture Card)
=============================================================================

Liest das HDMI-Signal der Switch über eine USB-Capture-Card ein.

Wichtig gegen Input-Lag:
  1. Fest 1280x720 @ 60 FPS (MJPG) anfordern.
  2. Puffergröße 1 — OpenCV darf den Frame nicht "sammeln".
  3. Lese-Thread läuft DAUERND und hält immer nur den NEUESTEN Frame.
     Wer später liest, kriegt nicht einen alten Frame, sondern den aktuellsten.

Test ohne Hardware:
  python helm_capture.py --test   (erzeugt ein Testbild mit Laufband)
"""

import threading
import time
import collections
import numpy as np
import cv2

# Zieleinstellungen — Switch (Handheld/Dock 720p-Modus)
TARGET_W = 1280
TARGET_H = 720
TARGET_FPS = 60


def open_capture(device=0):
    """Öffnet die Capture-Card mit festen Einstellungen (Plattformabhängig)."""
    import sys
    if sys.platform.startswith("win"):
        cap = cv2.VideoCapture(device + cv2.CAP_DSHOW)   # DirectShow: schnellster Weg auf Windows
    else:
        cap = cv2.VideoCapture(device, cv2.CAP_V4L2)     # Raspberry Pi / Linux

    if not cap.isOpened():
        return None

    # --- Festnageln: Auflösung, Framerate, Codec, Puffer ---
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))  # MJPG nötig, damit 720p60 über USB schafft
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, TARGET_W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, TARGET_H)
    cap.set(cv2.CAP_PROP_FPS, TARGET_FPS)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)                # der wichtigste Anti-Lag-Schalter

    # Zurücklesen, was die Karte WIRKLICH liefert
    real = {
        "w": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        "h": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        "fps": cap.get(cv2.CAP_PROP_FPS),
    }
    return cap, real


def make_test_frame(w=TARGET_W, h=TARGET_H, t=0.0):
    """Testbild (ohne Capture-Card): Farbverlauf + Laufband, um 60 FPS gefühlsmäßig zu prüfen."""
    frame = np.zeros((h, w, 3), dtype=np.uint8)
    frame[:, :, 0] = np.tile(np.linspace(40, 200, w).astype(np.uint8), (h, 1))
    frame[:, :, 2] = 30
    # Laufband: bewegt sich mit t -> prüft flüssige 60 FPS mit bloßem Auge
    x = int((t * 200) % (w + 200)) - 200
    cv2.rectangle(frame, (x, h // 2 - 60), (x + 200, h // 2 + 60), (0, 255, 255), -1)
    cv2.putText(frame, "TESTSIGNAL - KEINE CAPTURE CARD", (30, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2, cv2.LINE_AA)
    return frame


class SwitchCapture:
    """Neuester-Frame-Leser mit eigenem Thread und FPS-Messung."""

    def __init__(self, device=0, allow_test_signal=True):
        self.device = device
        self.allow_test_signal = allow_test_signal
        self._lock = threading.Lock()
        self._frame = None
        self._test_start = time.time()
        self._fps_hist = collections.deque(maxlen=60)
        self._dropped = 0
        self._running = False
        self._thread = None
        self.cap = None
        self.real = None

    # ---------- Lebenszyklus ----------

    def start(self):
        result = open_capture(self.device)
        if result is None:
            if not self.allow_test_signal:
                raise RuntimeError("Keine Capture-Card gefunden (Device %s)" % self.device)
            print("[Capture] Keine Capture-Card gefunden -> Testsignal an.")
            self.cap = None
        else:
            self.cap, self.real = result
            print("[Capture] Karte ok: %(w)dx%(h)d @ %(fps).1f FPS" % self.real)

        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        return self

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    # ---------- Intern ----------

    def _loop(self):
        next_fps_tick = time.time() + 1.0
        while self._running:
            if self.cap is None:
                # Testsignal erzeugen (ohne Hardware)
                frame = make_test_frame(t=time.time() - self._test_start)
                with self._lock:
                    self._frame = frame
                time.sleep(1.0 / TARGET_FPS)
            else:
                # GRAB ohne Dekodierung prüfen, RETRIEVAL nur wenn neu —
                # und danach sofort wieder von vorn: alte Frames werden weggeworfen.
                ok, frame = self.cap.read()
                if not ok:
                    self._dropped += 1
                    time.sleep(0.02)
                    continue
                with self._lock:
                    self._frame = frame

            now = time.time()
            self._fps_hist.append(now)
            if now >= next_fps_tick:
                next_fps_tick = now + 1.0

    # ---------- Abfrage ----------

    def read(self):
        """Gibt den NEUESTEN Frame zurück (oder None, wenn noch keiner da ist)."""
        with self._lock:
            if self._frame is None:
                return None
            return self._frame.copy()

    def fps(self):
        """Gemessene Eingangs-FPS der letzten Sekunde."""
        if len(self._fps_hist) < 2:
            return 0.0
        span = self._fps_hist[-1] - self._fps_hist[0]
        if span <= 0:
            return 0.0
        return (len(self._fps_hist) - 1) / span

    def status(self):
        return {
            "quelle": "Capture-Card" if self.cap is not None else "Testsignal",
            "aufloesung": "%dx%d" % (self.real["w"], self.real["h"]) if self.real else "%dx%d" % (TARGET_W, TARGET_H),
            "fps_eingang": round(self.fps(), 1),
            "verlorene_frames": self._dropped,
        }


# ---------------- Selbsttest ----------------
if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Schritt 1: Switch-Capture testen")
    ap.add_argument("--device", type=int, default=0, help="Capture-Card-Index (Standard 0)")
    ap.add_argument("--test", action="store_true", help="Nur Testsignal, keine Karte öffnen")
    args = ap.parse_args()

    cam = SwitchCapture(device=args.device, allow_test_signal=True)
    if args.test:
        cam.cap = None
        cam._running = True
        cam._thread = threading.Thread(target=cam._loop, daemon=True)
        cam._thread.start()
    else:
        cam.start()

    print("Fenster schließen (q) beendet. Gemeldete FPS müssen nahe an 60 liegen.")
    try:
        while True:
            frame = cam.read()
            if frame is None:
                time.sleep(0.05)
                continue
            st = cam.status()
            cv2.putText(frame, "%s  %s  %.1f FPS" % (st["quelle"], st["aufloesung"], st["fps_eingang"]),
                        (20, TARGET_H - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2, cv2.LINE_AA)
            cv2.imshow("Schritt 1: Capture-Test", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        cam.stop()
        cv2.destroyAllWindows()
