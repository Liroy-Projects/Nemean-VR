# -*- coding: utf-8 -*-
"""
helm_funktionen_2.py — Aufgabenblatt 2: Helm-Steuerlogik
=========================================================

1. soll_frame_rendern        — FPS-Throttle: HUD nur rendern, wenn fällig
2. waehle_video_quelle       — Umschalter Switch <-> Passthrough <-> Blank
3. formatiere_latenz_anzeige — Latenz-Indikator fürs HUD
4. berechne_helm_lautstaerke — Lautstärke-Kompensation gegen Lüfterlärm

Alle vier Funktionen sind pur (keine Hardware, kein OpenCV) und damit
einzeln testbar:  python helm_funktionen_2.py
"""


# ============================================================
# Aufgabe 1: Das FPS-Throttle für das HUD
# ============================================================

def soll_frame_rendern(letzter_frame_zeit, aktueller_zeitstempel, ziel_fps):
    """Entscheidet, ob das HUD jetzt einen Frame rendern darf.

    Der Pi rendert nur, wenn seit dem letzten Frame das volle Intervall
    vergangen ist — so bleibt das HUD stabil bei z. B. 30 FPS und der
    Prozessor wird nicht durch unnötige Frames heiß.

    Eingabe:
        letzter_frame_zeit   (float) — Zeitstempel des letzten Frames
        aktueller_zeitstempel (float) — Zeitstempel jetzt
        ziel_fps             (int)   — gewünschte Bilder pro Sekunde

    Regeln:
        - ziel_fps <= 0  -> sofort False (Division durch 0 verhindern)
        - Intervall = 1 / ziel_fps
        - verstrichene Zeit >= Intervall -> True, sonst False

    Rückgabe:
        True oder False
    """
    # Regel 1: Unsinniges Ziel (0 oder negativ) -> nie rendern
    if ziel_fps <= 0:
        return False

    # Regel 2: Abstand zwischen zwei Frames in Sekunden
    intervall = 1 / ziel_fps

    # Regel 3: Ist genug Zeit vergangen?
    vergangen = aktueller_zeitstempel - letzter_frame_zeit
    return vergangen >= intervall


# ============================================================
# Aufgabe 2: Der Video-Quellen-Umschalter
# ============================================================

def waehle_video_quelle(aktueller_modus, taste_gedrueckt, kamera_fehler):
    """Entscheidet, welches Bild auf die Helm-Displays kommt.

    Eingabe:
        aktueller_modus  (str)  — "SWITCH", "PASSTHROUGH" oder "BLANK"
        taste_gedrueckt  (bool) — Quellen-Taste am Helm gedrückt?
        kamera_fehler    (bool) — Passthrough-Kamera defekt?

    Regeln:
        - kamera_fehler  -> sofort "BLANK" mit Fehler-Text
        - Taste gedrückt -> SWITCH <-> PASSTHROUGH tauschen,
                            BLANK geht zu PASSTHROUGH
        - Taste nicht gedrückt -> alles bleibt, wie es ist

    Rückgabe:
        Tuple (neuer_modus, status_text)
    """
    # Regel 1: Kamera defekt schlägt ALLES — sofort schwarzes Bild
    if kamera_fehler:
        return ("BLANK", "FEHLER: Kamera ausgefallen")

    # Regel 2: Tastendruck schaltet die Quelle um
    if taste_gedrueckt:
        if aktueller_modus == "SWITCH":
            return ("PASSTHROUGH", "Kamera aktiv")
        if aktueller_modus == "PASSTHROUGH":
            return ("SWITCH", "Switch aktiv")
        # "BLANK" (oder ein unbekannter Modus) -> auf die Kamera
        return ("PASSTHROUGH", "Kamera aktiv")

    # Regel 3: Kein Tastendruck -> Modus bleibt, Text passt sich an
    if aktueller_modus == "SWITCH":
        return ("SWITCH", "Switch aktiv")
    if aktueller_modus == "PASSTHROUGH":
        return ("PASSTHROUGH", "Kamera aktiv")
    return ("BLANK", "Kein Signal")


# ============================================================
# Aufgabe 3: Der Latenz-Indikator
# ============================================================

def formatiere_latenz_anzeige(latenz_ms):
    """Formatiert die Bildverzögerung für das HUD — mit Ampel-Bewertung.

    Eingabe:
        latenz_ms (float/int) — Verzögerung in Millisekunden, z. B. 18.432

    Regeln:
        - Negative Werte -> auf 0.0 korrigieren
        - Zahl exakt auf 1 Nachkommastelle gerundet
        - <= 20.0 ms          -> "[PERFEKT] x.x ms"
        - 20.0 < x <= 50.0    -> "[OK] x.x ms"
        - > 50.0 ms           -> "[LAG WARNUNG] x.x ms"

    Rückgabe:
        Formatierter String, z. B. "[PERFEKT] 18.4 ms"
    """
    # Regel 1: Unsinnige negative Werte abfangen
    if latenz_ms < 0.0:
        latenz_ms = 0.0

    # Regel 2: ZUERST runden, DANN einordnen — so passen Anzeige
    # und Kategorie immer zusammen (20.04 zeigt "20.0" als PERFEKT,
    # statt als OK mit einem "20.0" im Text).
    wert = round(latenz_ms, 1)

    # Regel 3: Kategorie
    if wert <= 20.0:
        return "[PERFEKT] %.1f ms" % wert
    if wert <= 50.0:
        return "[OK] %.1f ms" % wert
    return "[LAG WARNUNG] %.1f ms" % wert


# ============================================================
# Aufgabe 4: Automatische Lautstärke-Kompensation
# ============================================================

def berechne_helm_lautstaerke(basis_lautstaerke, luefter_speed):
    """Hebt die Lautstärke an, wenn die Helmlüfter lauter werden.

    Eingabe:
        basis_lautstaerke (int) — Grundlautstärke 0..100
        luefter_speed     (int) — aktuelle Lüfterdrehzahl 0..100

    Regeln:
        - pro volle 25 % Lüftergeschwindigkeit +5 % Lautstärke
          (luefter_speed // 25 * 5)
        - Ergebnis auf 0..100 klemmen

    Rückgabe:
        int zwischen 0 und 100
    """
    # Regel 1: Bonus pro vollem 25-%-Schritt
    bonus = luefter_speed // 25 * 5

    # Regel 2: Bonus auf die Basis drauf
    ergebnis = basis_lautstaerke + bonus

    # Regel 3: Klemmen — nie über 100, nie unter 0
    return max(0, min(100, ergebnis))


# ============================================================
# Selbsttest — läuft bei direktem Aufruf:  python helm_funktionen_2.py
# ============================================================

if __name__ == "__main__":
    print("=" * 56)
    print(" Selbsttest: helm_funktionen_2.py")
    print("=" * 56)

    print("\n--- Aufgabe 1: FPS-Throttle ---")
    print("  ziel_fps=0            ->", soll_frame_rendern(0.0, 0.1, 0))
    print("  ziel_fps=-5           ->", soll_frame_rendern(0.0, 0.1, -5))
    print("  30 FPS, 1/30 s her    ->", soll_frame_rendern(0.0, 1 / 30, 30))
    print("  30 FPS, 0.03 s her    ->", soll_frame_rendern(0.0, 0.03, 30))
    print("  30 FPS, 0.04 s her    ->", soll_frame_rendern(0.0, 0.04, 30))
    print("  2 FPS, 0.5 s her      ->", soll_frame_rendern(10.0, 10.5, 2))

    print("\n--- Aufgabe 2: Quellen-Umschalter ---")
    print("  Fehler (aus SWITCH)   ->", waehle_video_quelle("SWITCH", False, True))
    print("  Fehler (aus BLANK)    ->", waehle_video_quelle("BLANK", True, True))
    print("  Taste, von SWITCH     ->", waehle_video_quelle("SWITCH", True, False))
    print("  Taste, von PASSTHRU   ->", waehle_video_quelle("PASSTHROUGH", True, False))
    print("  Taste, von BLANK      ->", waehle_video_quelle("BLANK", True, False))
    print("  keine Taste, SWITCH   ->", waehle_video_quelle("SWITCH", False, False))
    print("  keine Taste, PASSTHRU ->", waehle_video_quelle("PASSTHROUGH", False, False))
    print("  keine Taste, BLANK    ->", waehle_video_quelle("BLANK", False, False))

    print("\n--- Aufgabe 3: Latenz-Anzeige ---")
    for ms in (-5, 0, 18.432, 20.0, 20.1, 35.1, 50.0, 50.1, 82.0):
        print("  %8.3f ms -> %s" % (ms, formatiere_latenz_anzeige(ms)))

    print("\n--- Aufgabe 4: Lautstärke-Kompensation ---")
    for basis, luefter in ((60, 0), (60, 24), (60, 25), (60, 50), (60, 100),
                           (95, 100), (100, 100), (10, 100), (0, 0)):
        print("  Basis %3d %% + Lüfter %3d %% -> %3d %%" % (
            basis, luefter, berechne_helm_lautstaerke(basis, luefter)))

    print("\nFertig.")
