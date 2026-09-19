# -*- coding: utf-8 -*-
"""
helm_vr_renderer.py — Schritt 2: Split-Screen & Optik (VR-Linsen)
==================================================================

Macht aus einem Spiel-Frame das VR-Bild:
  1. Split-Screen: linke Bildhälfte -> linkes Auge, rechte -> rechtes Auge
     (Alternativ: JEDEM Auge das GANZE Bild — Modus "dup", gut ohne Switch-Umbau.)
  2. Zentrierung: Bild wird im Auge-Panel zentriert und passend skaliert
     (Zoom > 1 schneidet den schwarzen Rand ab, den die Verzerrung am Rand erzeugt).
  3. Barrel-Distortion (Fischaugen-Gegenstück): gleicht die Wölbung der VR-Linsen
     aus, damit das Bild durch die Linse wieder gerade aussieht.

Geschwindigkeit: Die Verzerrung wird als Remap-Tabelle (LUT) EINMAL vorberechnet.
Pro Frame bleibt nur cv2.remap pro Auge — auf einem Pi 4 realistisch 60 FPS.

Test ohne VR-Brille: python helm_vr_renderer.py --test
"""

import numpy as np
import cv2

# Panel-Einstellungen (Auf dem Pi gängig: 2x quadratische Augen-Panels)
PANEL_W = 720          # Breite eines Augen-Panels
PANEL_H = 720          # Höhe eines Augen-Panels
LENS_K1 = 0.18         # Barrel-Stärke: Linsenwölbung (0 = aus, 0.10..0.30 typisch)
LENS_K2 = 0.06         # zweiter Verzerrungsterm (feinjustieren)
EDGE_SCALE = 1.25      # Zoom: schneidet den verzerrten Schwarzwand-Rand ab


def split_frame(frame, mode="half"):
    """Teilt den Frame in linkes/rechtes Bild.

    mode="half": Switch-SBS-Ausgabe — linke Hälfte -> linkes Auge, rechte -> rechtes.
    mode="dup":  beide Augen bekommen das GANZE Bild (alles sehen, ohne Umbau).
    """
    h, w = frame.shape[:2]
    if mode == "half":
        mid = w // 2
        left = frame[:, :mid]
        right = frame[:, mid:]
    else:
        left = frame
        right = frame
    return left, right


def _build_remap_lut(src_w, src_h, dst_w, dst_h, k1, k2, edge_scale):
    """Erzeugt die Remap-Tabellen für Barrel-Distortion + Zentrierung + Skalierung.

    Für jeden Pixel des Auge-Panels wird berechnet, WO im Quellbild er
    hinschauen muss — das ist exakt die Umkehrung der Linsenwölbung.
    """
    # Normierte Koordinaten des Panels, Zentrum = (0,0), Rand = 1
    xs = np.linspace(-1.0, 1.0, dst_w, dtype=np.float32)
    ys = np.linspace(-1.0, 1.0, dst_h, dtype=np.float32)
    xx, yy = np.meshgrid(xs, ys)

    # Barrel-Distortion (inverse Abbildung): Rand wird nach außen gezogen,
    # damit die Linse es wieder einrollt. r -> r * (1 + k1*r² + k2*r⁴)
    r2 = xx * xx + yy * yy
    factor = 1.0 + k1 * r2 + k2 * r2 * r2
    map_x = xx * factor
    map_y = yy * factor

    # Zoom gegen den Schwarzwand-Rand + Rückrechnung in Pixel des Quellbilds
    half_src_w = src_w / 2.0 / edge_scale
    half_src_h = src_h / 2.0 / edge_scale
    lut_x = (map_x * half_src_w + src_w / 2.0).astype(np.float32)
    lut_y = (map_y * half_src_h + src_h / 2.0).astype(np.float32)
    return lut_x, lut_y


class VRRenderer:
    """Hält die Remap-LUTs und rendert beide Augen-Panels pro Frame."""

    def __init__(self, panel_w=PANEL_W, panel_h=PANEL_H,
                 k1=LENS_K1, k2=LENS_K2, edge_scale=EDGE_SCALE):
        self.panel_w = panel_w
        self.panel_h = panel_h
        self._lut_cache = {}   # (src_w, src_h) -> (lut_x, lut_y)
        self.k1 = k1
        self.k2 = k2
        self.edge_scale = edge_scale

    def _lut_for(self, src_w, src_h):
        key = (src_w, src_h)
        if key not in self._lut_cache:
            self._lut_cache[key] = _build_remap_lut(
                src_w, src_h, self.panel_w, self.panel_h,
                self.k1, self.k2, self.edge_scale)
        return self._lut_cache[key]

    def render(self, frame, mode="dup"):
        """Erzeugt das Doppel-Panel: links Auge, rechts Auge, IPD-Mitte frei."""
        left_src, right_src = split_frame(frame, mode)

        out = np.zeros((self.panel_h, self.panel_w * 2 + 20, 3), dtype=np.uint8)
        cx0 = (out.shape[1] - self.panel_w * 2) // 2      # 10 px schwarze Nasenbrücke

        for i, src in enumerate((left_src, right_src)):
            lut_x, lut_y = self._lut_for(src.shape[1], src.shape[0])
            panel = cv2.remap(src, lut_x, lut_y, cv2.INTER_LINEAR,
                              borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
            x0 = cx0 + i * (self.panel_w + (20 if i == 0 else 0))
            out[:, x0:x0 + self.panel_w] = panel

        # Feinjustage-Hilfe: Fadenkreuz in jeder Panel-Mitte
        for cx in (cx0 + self.panel_w // 2, out.shape[1] - self.panel_w // 2):
            cv2.drawMarker(out, (cx, self.panel_h // 2), (0, 255, 0),
                           cv2.MARKER_CROSS, 24, 1)
        return out


# ---------------- Selbsttest ----------------
if __name__ == "__main__":
    import argparse, time
    ap = argparse.ArgumentParser(description="Schritt 2: VR-Renderer testen")
    ap.add_argument("--mode", choices=["dup", "half"], default="dup")
    ap.add_argument("--k1", type=float, default=LENS_K1, help="Barrel-Stärke")
    ap.add_argument("--edge", type=float, default=EDGE_SCALE, help="Rand-Zoom")
    args = ap.parse_args()

    # Bewegtes Testmuster: Grid + Kreis + Text
    t = 0
    renderer = VRRenderer(k1=args.k1, edge_scale=args.edge)
    print("Fenster schließen (q) beendet. Tasten: [ ] = k1 +/-, , = Zoom -")
    while True:
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        for x in range(0, 1280, 64):
            cv2.line(frame, (x, 0), (x, 720), (60, 60, 60), 1)
        for y in range(0, 720, 64):
            cv2.line(frame, (0, y), (1280, y), (60, 60, 60), 1)
        cx = int(640 + 300 * np.cos(t / 30.0))
        cy = int(360 + 200 * np.sin(t / 30.0))
        cv2.circle(frame, (cx, cy), 40, (0, 200, 255), -1)
        cv2.putText(frame, "LINKS", (40, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
        cv2.putText(frame, "RECHTS", (940, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)

        t0 = time.time()
        vr = renderer.render(frame, mode=args.mode)
        dt = (time.time() - t0) * 1000

        cv2.putText(vr, "render: %.1f ms (%.0f FPS moeglich)  k1=%.2f" % (dt, 1000 / max(dt, 1e-6), args.k1),
                    (20, vr.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.imshow("Schritt 2: VR-Renderer", vr)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        elif key == ord("["):
            args.k1 = max(0.0, args.k1 - 0.01)
        elif key == ord("]"):
            args.k1 = min(0.5, args.k1 + 0.01)
        t += 1
    cv2.destroyAllWindows()
