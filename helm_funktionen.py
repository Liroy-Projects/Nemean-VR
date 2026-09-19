# -*- coding: utf-8 -*-
"""
helm_funktionen.py — Vier Bausteine für den LiroyVR-Helm
=========================================================

1. berechne_luefter_speed   — Lüfter-Kennlinie (Temperatur -> Prozent)
2. render_akku_balken       — Akkustand als ASCII-Balken fürs HUD
3. verarbeite_helm_befehl   — Sprachbefehl-Parser (Text -> Aktion)
4. ist_stimme_aktiv         — Audio-Noise-Gate (Stimme oder Rauschen?)

Alle Funktionen sind pur (keine Hardware, kein OpenCV) und damit
einzeln testbar:  python helm_funktionen.py
"""


# ============================================================
# Aufgabe 1: Die Lüfter-Kennlinie
# ============================================================

def berechne_luefter_speed(temperatur):
    """Berechnet die Lüfterdrehzahl in Prozent aus der CPU-Temperatur.

    Eingabe:
        temperatur (float) — CPU-Temperatur in °C, z. B. 52.5

    Regeln:
        - unter 40 °C  -> 0 %
        - über  70 °C  -> 100 % + Konsole-Warnung
        - 40..70 °C    -> linear hochlaufend (55 °C = exakt 50 %)

    Rückgabe:
        int zwischen 0 und 100
    """
    # Regel 1: kalt -> Lüfter aus
    if temperatur < 40:
        return 0

    # Regel 2: zu heiß -> voll aufdrehen und warnen
    if temperatur > 70:
        print("[WARNUNG] CPU bei %.1f °C (über 70 °C)! "
              "Lüfter auf 100 %% gesetzt." % temperatur)
        return 100

    # Regel 3: linear zwischen 40 °C (0 %) und 70 °C (100 %)
    prozent = (temperatur - 40) / (70 - 40) * 100

    # Kaufmännisch runden (int(x + 0.5)), dann sicherheitshalber
    # auf den Bereich 0..100 klemmen.
    return max(0, min(100, int(prozent + 0.5)))


# ============================================================
# Aufgabe 2: Der ASCII-Akkubalken
# ============================================================

def render_akku_balken(prozent):
    """Baut den Akkustand als Text-Grafik fürs HUD.

    Eingabe:
        prozent (int) — 0 bis 100

    Regeln:
        - Balken: 10 Zeichen in eckigen Klammern,
                  '█' = gefüllt, '░' = leer (60 % -> 6 + 4)
        - dahinter der Prozentwert als Text
        - unter 20 %: "![AKKU LOW]! " vor den Balken

    Rückgabe:
        String, z. B. "[██████░░░░] 60%"
    """
    # Sicherheitshalber klemmen, falls ein Sensor Unsinn liefert
    prozent = max(0, min(100, int(prozent)))

    gefuellt = prozent // 10          # 10 Blöcke, jeder = 10 %
    leer = 10 - gefuellt

    balken = "[" + ("█" * gefuellt) + ("░" * leer) + "]"
    text = "%s %d%%" % (balken, prozent)

    if prozent < 20:
        text = "![AKKU LOW]! " + text

    return text


# ============================================================
# Aufgabe 3: Der Helm-Sprachbefehl-Parser
# ============================================================

def verarbeite_helm_befehl(befehl_text):
    """Analysiert einen Sprachbefehl und liefert die Antwort von Liroy.

    Eingabe:
        befehl_text (str) — ein beliebiger Satz

    Regeln (Groß-/Kleinschreibung ist egal):
        - "lüfter" UND "max"  -> "Lüfter auf 100% gesetzt"
        - "hud" UND "aus"     -> "HUD ausgeblendet"
        - "status"            -> "System läuft normal"
        - nichts davon        -> "Befehl nicht verstanden"

    Rückgabe:
        Antwort-Text (str)
    """
    # Schritt 1: klein schreiben, damit Schreibweise keine Rolle spielt
    text = befehl_text.lower()

    # Regel 1: Lüfter auf Maximum
    if "lüfter" in text and "max" in text:
        return "Lüfter auf 100% gesetzt"

    # Regel 2: HUD ausblenden
    if "hud" in text and "aus" in text:
        return "HUD ausgeblendet"

    # Regel 3: Status-Abfrage
    if "status" in text:
        return "System läuft normal"

    # Regel 4: nichts erkannt
    return "Befehl nicht verstanden"


# ============================================================
# Aufgabe 4: Das Audio-Noise-Gate
# ============================================================

def ist_stimme_aktiv(audio_daten, schwellenwert):
    """Prüft, ob gesprochen wird oder nur Hintergrundrauschen da ist.

    Eingabe:
        audio_daten    (list) — Zahlen zwischen -1.0 und 1.0,
                                z. B. [-0.2, 0.5, 0.1, -0.4, 0.0]
        schwellenwert  (float) — z. B. 0.2

    Regeln:
        1. Alle Werte mit abs() positiv machen
        2. Durchschnitt berechnen
        3. Durchschnitt > Schwellenwert -> Stimme aktiv

    Rückgabe:
        True (Stimme erkannt) oder False (nur Rauschen)
    """
    # Leere Liste = keine Samples = keine Stimme (Division durch 0 vermeiden)
    if not audio_daten:
        return False

    # Schritt 1: alles positiv machen
    lautstaerken = [abs(wert) for wert in audio_daten]

    # Schritt 2: Durchschnitt — auf 10 Stellen gerundet, damit
    # Float-Artefakte (0.2+0.2+0.2 = 0.6000000000000001) nicht einen
    # Grenzfall fälschlich zu "Stimme aktiv" machen.
    durchschnitt = round(sum(lautstaerken) / len(lautstaerken), 10)

    # Schritt 3: Schwelle vergleichen
    return durchschnitt > schwellenwert


# ============================================================
# Selbsttest — läuft bei direktem Aufruf:  python helm_funktionen.py
# ============================================================

if __name__ == "__main__":
    print("=" * 56)
    print(" Selbsttest: helm_funktionen.py")
    print("=" * 56)

    print("\n--- Aufgabe 1: Lüfter-Kennlinie ---")
    fuer_temp = [30, 39.9, 40, 47.5, 55, 62.5, 70, 75.3]
    for t in fuer_temp:
        print("  %5.1f °C -> %3d %%" % (t, berechne_luefter_speed(t)))

    print("\n--- Aufgabe 2: Akku-Balken ---")
    fuer_akku = [100, 60, 45, 20, 19, 5, 0]
    for p in fuer_akku:
        print("  %3d %% -> %s" % (p, render_akku_balken(p)))

    print("\n--- Aufgabe 3: Sprachbefehle ---")
    fuer_befehl = [
        "Setz den LÜFTER auf MAX",
        "Mach bitte das HUD aus",
        "wie ist der Status?",
        "spiel mal Musik",
    ]
    for b in fuer_befehl:
        print("  %r -> %s" % (b, verarbeite_helm_befehl(b)))

    print("\n--- Aufgabe 4: Noise-Gate ---")
    tests = [
        ([-0.2, 0.5, 0.1, -0.4, 0.0], 0.2),   # Beispiel aus der Aufgabe
        ([-0.05, 0.05, 0.02, -0.03], 0.2),    # leises Rauschen
        ([0.9, -0.8, 0.7], 0.2),              # laute Stimme
    ]
    for daten, schwelle in tests:
        avg = sum(abs(x) for x in daten) / len(daten)
        print("  avg=%.3f > %.2f ? -> %s" % (avg, schwelle, ist_stimme_aktiv(daten, schwelle)))

    print("\nFertig.")
