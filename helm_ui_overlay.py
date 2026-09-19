# -*- coding: utf-8 -*-
"""
helm_ui_overlay.py — Schritt 3: Das Liroy-HUD (visuelles Interface)
====================================================================

Legt Text, Rahmen und Statusanzeigen ÜBER das (geteilte) VR-Bild:
  - Uhrzeit
  - CPU-Temperatur (vom Pi oder vom Host)
  - Liroy-Status (fragt den laufenden Liroy-Server ab, fällt zurück auf "offline")
  - FPS / Quelle

Alles wird erst auf eine TRANSPARENTE Ebene gezeichnet und dann mit
cv2.addWeighted() über das Bild gemischt — dadurch bleibt das Spiel klar
sichtbar und das HUD wirkt halbdurchlässig wie ein echtes Visier.

Test: python helm_ui_overlay.py
"""

import time
import datetime
import urllib.request
import json
import numpy as np
import cv2

# --- Look & Feel des HUD ---
HUD_ALPHA = 0.45          # Transparenz: 0 = unsichtbar, 1 = voll deckend
HUD_COLOR = (180, 255, 120)     # Liroy-Grün (BGR)
WARN_COLOR = (80, 120, 255)     # Orange für Warnungen (BGR)
ALARM_COLOR = (80, 80, 255)     # Rot für Kritisch (BGR)
FONT = cv2.FONT_HERSHEY_SIMPLEX

LIROY_STATUS_URL = "http://127.0.0.1:8080/api/health"   # dein Liroy-Server
STATUS_CACHE_TTL = 5.0                                  # Status max. alle 5 s neu fragen


def read_cpu_temp():
    """CPU-Temperatur lesen — Pi: thermal_zone0, sonst psutil, sonst None."""
    try:
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            return float(f.read().strip()) / 1000.0
    except Exception:
        pass
    try:
        import psutil
        t = psutil.sensors_temperatures()
        for key in ("cpu_thermal", "coretemp", "k10temp"):
            if key in t and t[key]:
                return float(t[key][0].current)
    except Exception:
        pass
    return None


class LiroyHud:
    """Zeichnet das HUD auf eine transparente Ebene und mischt sie aufs Bild."""

    def __init__(self, liroy_url=LIROY_STATUS_URL):
        self.liroy_url = liroy_url
        self._status_cache = None
        self._status_time = 0.0

    # ---------- Liroy-Status (mit Cache, blockiert nie lange) ----------

    def _liroy_status(self):
        now = time.time()
        if self._status_cache is not None and now - self._status_time < STATUS_CACHE_TTL:
            return self._status_cache
        status = {"online": False, "text": "Liroy: offline"}
        try:
            req = urllib.request.Request(self.liroy_url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                data = json.loads(resp.read().decode("utf-8", "replace"))
            # Felder unterschiedlich benannt — das Wichtigste rausfischen:
            pieces = []
            for key, label in (("nodes", "Knoten"), ("edges", "Verbindungen"),
                               ("connections", "Verbindungen"), ("knowledge", "Wissen")):
                if key in data:
                    pieces.append("%s %s" % (label, data[key]))
            if data.get("ok") or data.get("status") == "online":
                status = {"online": True, "text": "Liroy: online" + (" · " + " · ".join(pieces) if pieces else "")}
            elif pieces:
                status = {"online": True, "text": "Liroy: online · " + " · ".join(pieces)}
        except Exception:
            pass
        self._status_cache = status
        self._status_time = now
        return status

    # ---------- Die Zeichnung ----------

    def draw(self, frame, extra=None):
        """Mischt das HUD auf `frame` (in place) und gibt Zusatzinfos zurück."""
        h, w = frame.shape[:2]
        extra = dict(extra or {})

        # 1) Transparente Ebene anlegen
        layer = frame.copy()
        overlay_done = np.zeros_like(frame)   # nur für farbige Bänder

        # Kopf-Band (halbdurchlässig)
        bar_h = 54
        cv2.rectangle(overlay_done, (0, 0), (w, bar_h), (30, 30, 30), -1)
        cv2.rectangle(overlay_done, (0, h - bar_h), (w, h), (30, 30, 30), -1)

        # Rahmen um das gesamte Sichtfeld
        cv2.rectangle(overlay_done, (6, 6), (w - 7, h - 7), HUD_COLOR, 2)

        # 2) Basis-Bänder mit addWeighted einmischen (Transparenz!)
        cv2.addWeighted(overlay_done, HUD_ALPHA, frame, 1.0 - HUD_ALPHA, 0, frame)

        # 3) Text auf einer KOPIER-Ebene (Text bleibt voll deckend = gut lesbar)
        temp = frame.copy()

        # --- Uhrzeit links oben ---
        now = datetime.datetime.now().strftime("%H:%M:%S")
        cv2.putText(temp, now, (20, 38), FONT, 1.0, HUD_COLOR, 2, cv2.LINE_AA)

        # --- CPU-Temperatur mittig oben ---
        temp_c = read_cpu_temp()
        if temp_c is None:
            t_text, t_color = "CPU: --", HUD_COLOR
        elif temp_c < 60:
            t_text, t_color = "CPU: %.1f C" % temp_c, HUD_COLOR
        elif temp_c < 75:
            t_text, t_color = "CPU: %.1f C !" % temp_c, WARN_COLOR
        else:
            t_text, t_color = "CPU: %.1f C !!" % temp_c, ALARM_COLOR
        (tw, _), _ = cv2.getTextSize(t_text, FONT, 1.0, 2)
        cv2.putText(temp, t_text, (w // 2 - tw // 2, 38), FONT, 1.0, t_color, 2, cv2.LINE_AA)

        # --- FPS / Quelle rechts oben ---
        right = "FPS %s  |  %s" % (extra.get("fps", "--"), extra.get("quelle", ""))
        (rw, _), _ = cv2.getTextSize(right, FONT, 0.8, 2)
        cv2.putText(temp, right, (w - rw - 20, 36), FONT, 0.8, HUD_COLOR, 2, cv2.LINE_AA)

        # --- Liroy-Status links unten ---
        st = self._liroy_status()
        st_color = HUD_COLOR if st["online"] else WARN_COLOR
        cv2.putText(temp, st["text"], (20, h - 18), FONT, 0.75, st_color, 2, cv2.LINE_AA)

        # --- Lüfter rechts unten (falls Schritt 4 läuft) ---
        fan_text = extra.get("fan", "")
        if fan_text:
            (fw, _), _ = cv2.getTextSize(fan_text, FONT, 0.75, 2)
            cv2.putText(temp, fan_text, (w - fw - 20, h - 18), FONT, 0.75, HUD_COLOR, 2, cv2.LINE_AA)

        # --- Hinweis-Mitte (z. B. "HUD: an") ---
        hint = extra.get("hint", "")
        if hint:
            (hw, _), _ = cv2.getTextSize(hint, FONT, 0.7, 2)
            cv2.putText(temp, hint, (w // 2 - hw // 2, h - 18), FONT, 0.7, (200, 200, 200), 2, cv2.LINE_AA)

        # Text voll deckend einblenden: Maske aus dem Unterschied
        diff = cv2.absdiff(temp, frame)
        mask = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(mask, 1, 255, cv2.THRESH_BINARY)
        np.copyto(frame, temp, where=mask[:, :, None].astype(bool))

        return {"liroy": st, "cpu": temp_c}


# ---------------- Selbsttest ----------------
if __name__ == "__main__":
    hud = LiroyHud()
    t = 0
    print("HUD-Test läuft. q = beenden.")
    while True:
        frame = np.full((720, 1280, 3), (40, 40, 40), dtype=np.uint8)
        cv2.putText(frame, "SPIELBILD-SIMULATION", (420, 370), FONT, 1.2, (90, 90, 90), 3)
        # bewegter Punkt, damit man Transparenz sieht
        cv2.circle(frame, (int(640 + 400 * np.sin(t / 20.0)), 360), 60, (0, 140, 255), -1)
        hud.draw(frame, extra={"fps": "%.0f" % (55 + 5 * np.sin(t / 10.0)),
                               "quelle": "Testsignal",
                               "fan": "Luefter: 45%%",
                               "hint": "HUD-Testmodus"})
        cv2.imshow("Schritt 3: Liroy-HUD", frame)
        if cv2.waitKey(33) & 0xFF == ord("q"):
            break
        t += 1
    cv2.destroyAllWindows()
