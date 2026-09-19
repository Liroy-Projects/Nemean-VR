# LiroyVR — Nintendo Switch im VR-Helm, mit Liroy-HUD

Vier Bausteine, ein Befehl:

```
helm_capture.py          (1) Switch-Bild rein, fest 720p60, kein Lag
helm_vr_renderer.py      (2) Split-Screen + Linsenzentrierung + Barrel-Distortion
helm_ui_overlay.py       (3) Liroy-HUD: Uhrzeit, CPU-Temp, Liroy-Status, Lüfter
helm_hardware_control.py (4) CPU-Temperatur lesen, Lüfter per PWM stufenlos
helm_main.py             alles zusammen
```

## Schnellstart am PC (ohne Hardware)

```bash
pip install opencv-python numpy
python helm_main.py --simulate
```

Du siehst ein Testsignal (bewegtes Laufband) in VR-Optik mit HUD — so
kannst du Optik und HUD fertig justieren, bevor die Switch dranhängt.

## Am Raspberry Pi mit echter Hardware

```bash
pip install opencv-python numpy gpiozero
sudo python helm_main.py            # GPIO braucht root
# oder ohne GPIO:
python helm_main.py --simulate
```

- Capture-Card: einfach einstecken; mehrere Karten? `--device 1`
- Switch im Dock an die Capture-Card anschließen (Handheld-Modus: 720p)

## Tasten im Helm-Fenster

| Taste | Wirkung |
|---|---|
| `h` | HUD an/aus |
| `v` | VR-Split/Verzerrung an/aus (rohes Bild) |
| `d` | Modus `dup` (beide Augen sehen alles) ↔ `half` (Switch-Seitenmodus) |
| `q` | beenden |

## Linsen-Justage (Barrel-Distortion)

Jede Brille wölbt anders. Zwei Schrauben:

1. `--k1 0.18` beim Start (0,10…0,30 typisch) — größere Zahl = stärkere Gegenwölbung
2. `EDGE_SCALE` in `helm_vr_renderer.py` (Standard 1,25) — Zoom gegen den
   schwarzen Rand, den die Verzerrung an den Ecken erzeugt.

Im Renderer-Test (`python helm_vr_renderer.py --test`... eigentlich ohne Argument)
kannst du mit `[` und `]` die Verzerrung live drehen, bis die Gitterlinien
durch die Linse gerade aussehen.

## Lüfter-Verdrahtung (Schritt 4)

```
GPIO 18 (Pin 12) --1kOhm--|  Basis  NPN (z.B. 2N2222 / BC547)
5V ----------------------|  Kollektor -> Lüfter+
GND ---------------------|  Emitter
Lüfter- -----------------|  GND  (gemeinsame Masse mit Pi!)
```

Die PWM läuft mit 25 kHz (PC-Lüfter-Norm, unhörbar). Die Kurve steht in
`FAN_CURVE` in `helm_hardware_control.py`:

| Temperatur | Lüfter |
|---|---|
| unter 45 °C | aus |
| 45–55 °C | 30–60 % (linear) |
| über 65 °C | 100 % |

**Immer über einen Transistor schalten — GPIO-Pins vertragen keinen Motorstrom!**

## Liroy-Anbindung (Schritt 3)

Das HUD fragt `http://127.0.0.1:8080/api/status` ab und zeigt, ob Liroy
online ist. Läuft der Helm auf einem anderen Gerät als der Liroy-Server,
URL oben in `helm_ui_overlay.py` (`LIROY_STATUS_URL`) anpassen.

## Fehlerbehebung

| Problem | Lösung |
|---|---|
| Bild ruckelt | Lüfter/CPU-Last prüfen; `--panel 480` probieren |
| Bild verzerrt falsch | `--k1` anpassen (live mit `[` `]` im Renderer-Test) |
| Schwarzer Rand rundum | `EDGE_SCALE` erhöhen (z. B. 1.4) |
| Kein Signal | `--device 1`, Switch einschalten, Karte prüfen (`dmesg` am Pi) |
| Lüfter dreht nicht | gpiozero installiert? `--simulate` zum Testen der Kurve |
