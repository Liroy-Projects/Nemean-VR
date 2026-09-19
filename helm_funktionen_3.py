# -*- coding: utf-8 -*-
"""
helm_funktionen_3.py — Aufgabenblatt 3: Sensorik & Schnellaktionen
===================================================================

1. glaette_sensor_werte             — Ringpuffer (Sliding Window) gegen flackerndes HUD
2. hole_hoechste_prioritaet_warnung — Nur die dringendste Warnung aufs HUD
3. berechne_restlaufzeit            — Akku-Restlaufzeit inkl. Lüfter-Zusatzlast
4. parse_gesten_sequenz             — Tasten-Kombinationen für Schnell-Aktionen

Alle vier Funktionen sind pur und einzeln testbar:
    python helm_funktionen_3.py
"""

import math


# ============================================================
# Aufgabe 1: Der Gleitende Sensor-Filter
# ============================================================

def glaette_sensor_werte(werte_historie, neuer_wert, fenster_groesse):
    """Fügt einen Sensorwert in den Ringpuffer ein und glättet über das Fenster.

    Eingabe:
        werte_historie  (list) — bisherige Messwerte (wird NICHT verändert)
        neuer_wert      (float) — der frische Messwert
        fenster_groesse (int)   — maximale Anzahl Werte im Fenster (> 0)

    Regeln:
        - neuer_wert kommt an eine KOPIE der Historie (Original bleibt unangetastet)
        - Fenster überläuft -> älteste Werte vorne abschneiden,
          sodass exakt die neuesten fenster_groesse übrig bleiben
        - fenster_groesse <= 0: Liste bleibt unverändert,
          Mittelwert ist round(neuer_wert, 2)
        - Mittelwert der bereinigten Liste, gerundet auf 2 Nachkommastellen

    Rückgabe:
        Tuple (aktualisierte_historie_liste, gerundeter_mittelwert)
    """
    # Sonderfall: ungueltiges Fenster -> gar nichts tun
    if fenster_groesse <= 0:
        return (list(werte_historie), round(neuer_wert, 2))

    # 1) Kopie anlegen und den neuen Wert anhängen
    historie = list(werte_historie)
    historie.append(neuer_wert)

    # 2) Überlauf: älteste Elemente vorne abschneiden
    if len(historie) > fenster_groesse:
        historie = historie[-fenster_groesse:]

    # 3) Geglätteter Mittelwert
    mittelwert = round(sum(historie) / len(historie), 2)

    return (historie, mittelwert)


# ============================================================
# Aufgabe 2: Der Warnungs-Prioritäts-Manager
# ============================================================

def hole_hoechste_prioritaet_warnung(aktive_warnungen):
    """Wählt die dringendste Warnung — nur sie darf aufs HUD.

    Eingabe:
        aktive_warnungen (list) — Dictionaries mit "typ", "prio", "text"

    Regeln:
        - leere Liste                      -> None
        - Einträge mit prio < 1            -> werden ignoriert
        - höchste prio gewinnt
        - Gleichstand: der WEITER VORN stehende Eintrag gewinnt
        - alle ignoriert                   -> None

    Rückgabe:
        Der "text"-String der Gewinner-Warnung (oder None)
    """
    if not aktive_warnungen:
        return None

    bester_text = None
    bestes_prio = None

    for warnung in aktive_warnungen:
        prio = warnung.get("prio", 0)
        if prio < 1:                       # Regel: ungueltige Prioritaet ignorieren
            continue
        # Strikt groesser -> bei Gleichstand gewinnt der frühere Eintrag
        if bestes_prio is None or prio > bestes_prio:
            bestes_prio = prio
            bester_text = warnung.get("text")

    return bester_text


# ============================================================
# Aufgabe 3: Akku-Restlaufzeit-Extrapolation
# ============================================================

def berechne_restlaufzeit(akku_prozent, verbrauch_pro_min, luefter_speed):
    """Rechnet aus, wie lange der Akku noch hält — Lüfter fressen extra.

    Eingabe:
        akku_prozent     (float) — Ladestand 0..100
        verbrauch_pro_min (float) — Grundverbrauch in %/min
        luefter_speed    (int)   — Lüfterdrehzahl 0..100

    Regeln:
        - akku auf 0..100 und Lüfter auf 0..100 klemmen
        - akku <= 0 oder verbrauch <= 0 -> (0, 0)
        - effektiver_verbrauch = verbrauch * (1.0 + luefter/100 * 0.3)
          (100 % Lüfter = +30 % Verbrauch)
        - gesamt_minuten = floor(akku / effektiver_verbrauch)
        - auf Stunden + Restminuten aufteilen

    Rückgabe:
        Tuple (stunden, minuten) — zwei Ganzzahlen
    """
    # Regel 1: Klemmen
    akku_prozent = max(0.0, min(100.0, float(akku_prozent)))
    luefter_speed = max(0, min(100, int(luefter_speed)))

    # Regel 2: Nichts zu rechnen
    if akku_prozent <= 0 or verbrauch_pro_min <= 0:
        return (0, 0)

    # Regel 3: Lüfter-Zusatzlast einpreisen (100 % Lüfter = +30 %)
    effektiver_verbrauch = verbrauch_pro_min * (1.0 + (luefter_speed / 100.0) * 0.3)

    # Regel 4: Restminuten
    gesamt_minuten = math.floor(akku_prozent / effektiver_verbrauch)

    # Regel 5: In Stunden und Restminuten teilen
    stunden = gesamt_minuten // 60
    minuten = gesamt_minuten % 60

    return (stunden, minuten)


# ============================================================
# Aufgabe 4: Gesten-Sequenz-Parser
# ============================================================

def parse_gesten_sequenz(eingabe_liste, ziel_sequenz):
    """Erkennt eine zusammenhängende Tasten-Kombination (z. B. Nachtsicht an).

    Eingabe:
        eingabe_liste (list) — reingekommene Gesten-Tokens, evtl. mit Müll
        ziel_sequenz  (list) — die registrierte Kombination

    Regeln:
        - Nur gültige Tokens bleiben: "TAP", "HOLD", "DOUBLE_TAP", "RELEASE"
        - ziel_sequenz leer ODER bereinigte Eingabe kürzer -> False
        - ziel_sequenz muss als ZUSAMMENHÄNGENDE Teilabfolge vorkommen

    Rückgabe:
        True (exakt am Stück gefunden) oder False
    """
    erlaubt = {"TAP", "HOLD", "DOUBLE_TAP", "RELEASE"}

    # Regel 1: Müll rausfiltern
    bereinigt = [token for token in eingabe_liste if token in erlaubt]

    # Regel 2: Leeres Ziel oder zu wenig Eingabe
    if not ziel_sequenz or len(bereinigt) < len(ziel_sequenz):
        return False

    # Regel 3: Gleitendes Fenster über die bereinigte Liste
    fenster = len(ziel_sequenz)
    for start in range(len(bereinigt) - fenster + 1):
        if bereinigt[start:start + fenster] == ziel_sequenz:
            return True
    return False


# ============================================================
# Selbsttest — läuft bei direktem Aufruf:  python helm_funktionen_3.py
# ============================================================

if __name__ == "__main__":
    print("=" * 56)
    print(" Selbsttest: helm_funktionen_3.py")
    print("=" * 56)

    print("\n--- Aufgabe 1: Sensor-Filter ---")
    print("  neu rein, Fenster passt    ->", glaette_sensor_werte([20.0, 22.0], 24.0, 3))
    print("  Überlauf, älteste fliegen  ->", glaette_sensor_werte([1.0, 2.0, 3.0], 4.0, 2))
    print("  Fenster 1 (nur Neustes)    ->", glaette_sensor_werte([5.0], 9.0, 1))
    print("  Fenster 0 (unverändert)    ->", glaette_sensor_werte([1.0, 2.0], 9.0, 0))
    print("  Fenster -3 (unverändert)   ->", glaette_sensor_werte([1.0, 2.0], 9.0, -3))

    print("\n--- Aufgabe 2: Prioritäts-Manager ---")
    print("  leer                       ->", hole_hoechste_prioritaet_warnung([]))
    print("  normal                     ->", hole_hoechste_prioritaet_warnung(
        [{"typ": "AKKU", "prio": 3, "text": "AKKU LOW"},
         {"typ": "HITZE", "prio": 5, "text": "OVERHEAT"}]))
    print("  Gleichstand, vorne gewinnt ->", hole_hoechste_prioritaet_warnung(
        [{"typ": "A", "prio": 5, "text": "ERSTE"},
         {"typ": "B", "prio": 5, "text": "ZWEITE"}]))
    print("  alle prio < 1              ->", hole_hoechste_prioritaet_warnung(
        [{"typ": "X", "prio": 0, "text": "MUELL"},
         {"typ": "Y", "prio": -2, "text": "AUCH MUELL"}]))
    print("  Negatives wird ignoriert   ->", hole_hoechste_prioritaet_warnung(
        [{"typ": "X", "prio": -2, "text": "WEG"},
         {"typ": "Y", "prio": 3, "text": "OK"}]))

    print("\n--- Aufgabe 3: Restlaufzeit ---")
    print("  100%, 0.7 %/min, Lüfter 0  ->", berechne_restlaufzeit(100, 0.7, 0))
    print("  50%, 0.5 %/min, Lüfter 100 ->", berechne_restlaufzeit(50, 0.5, 100))
    print("  10%, 0.5 %/min, Lüfter 0   ->", berechne_restlaufzeit(10, 0.5, 0))
    print("  Akku 0                     ->", berechne_restlaufzeit(0, 0.5, 50))
    print("  Akku negativ (geklemmt)    ->", berechne_restlaufzeit(-5, 0.5, 0))
    print("  Verbrauch 0                ->", berechne_restlaufzeit(80, 0, 50))
    print("  Lüfter 150 (geklemmt)      ->", berechne_restlaufzeit(100, 1.0, 150))
    print("  Akku 150 (geklemmt)        ->", berechne_restlaufzeit(150, 1.0, 0))

    print("\n--- Aufgabe 4: Gesten-Parser ---")
    print("  direkt am Stück            ->", parse_gesten_sequenz(
        ["TAP", "HOLD", "TAP"], ["HOLD", "TAP"]))
    print("  Müll dazwischen, überbrückt->", parse_gesten_sequenz(
        ["TAP", "INVALID", "HOLD", "TAP"], ["HOLD", "TAP"]))
    print("  Müll wird vorher gefiltert ->", parse_gesten_sequenz(
        ["TAP", "PAUSE", "TAP"], ["TAP", "TAP"]))   # -> True: nach Filterung sind die TAPs aneinander
    print("  keine Übereinstimmung      ->", parse_gesten_sequenz(
        ["TAP", "HOLD"], ["HOLD", "TAP"]))
    print("  leeres Ziel                ->", parse_gesten_sequenz(["TAP"], []))
    print("  Ziel länger als Eingabe    ->", parse_gesten_sequenz(
        ["TAP"], ["TAP", "HOLD", "RELEASE"]))
    print("  Groß/Klein strikt          ->", parse_gesten_sequenz(
        ["tap", "HOLD"], ["TAP", "HOLD"]))

    print("\nFertig.")
