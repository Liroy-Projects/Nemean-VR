# -*- coding: utf-8 -*-
"""
helm_hardware_control.py — Schritt 4: Sensoren & Kühlung (Raspberry Pi GPIO)
=============================================================================

- Liest die CPU-Temperatur:  /sys/class/thermal/thermal_zone0/temp
- Steuert den Lüfter STUFENLOS per PWM (Software-PWM über gpiozero)
- Lüfter-Drehzahl passend zur Temperatur:
      unter 45 C  -> aus
      45..55 C    -> leise (30 %)
      55..65 C    -> mittel (60 %)
      über 65 C   -> voll (100 %)
  (Werte oben frei änderbar — siehe FAN_CURVE)

Funktioniert auch am PC zum Testen: Temperatur wird gelesen, PWM nur geloggt.

Verdrahtung (Pi):
  GPIO 18 (Pin 12)  -> Basis des Transistors über 1 kOhm
  Lüfter+           -> 5V, Lüfter- -> Kollektor, Emitter -> GND
  (Immer Transistor nutzen — GPIO-Pins vertragen keinen Motorstrom!)

Test:  sudo python helm_hardware_control.py --test
"""

import time
import subprocess

# --- Lüfter-Kurve: (Temperatur, PWM-%) — dazwischen wird linear interpoliert ---
FAN_CURVE = [
    (40, 0),      # kühl -> aus
    (45, 30),     # starting to warm -> leise
    (55, 60),     # warm -> mittel
    (65, 100),    # heiß -> voll
]
PWM_PIN = 18          # GPIO18 = Hardware-PWM-fähig (Pin 12)
PWM_FREQUENCY = 25000  # 25 kHz: PC-Lüfter-Norm, hörbar leise (kein Brummen)
HYSTERESIS = 3.0       # °C Puffer, damit der Lüfter nicht flackert


def read_cpu_temp():
    """CPU-Temperatur in °C aus dem Sysfs des Pi — null Abhängigkeiten."""
    try:
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            return float(f.read().strip()) / 1000.0
    except Exception:
        pass
    # Fallback am PC (zum Testen): vcgencmd beim Raspberry Pi OS auf x86? Nein —
    # psutil probieren, sonst None.
    try:
        import psutil
        t = psutil.sensors_temperatures()
        for key in ("cpu_thermal", "coretemp", "k10temp", "acpitz"):
            if key in t and t[key]:
                return float(t[key][0].current)
    except Exception:
        pass
    return None


def pwm_percent_for_temp(temp_c, current_percent):
    """Lüfter-Prozent aus der Kurve — mit Hysterese, damit nichts flackert."""
    if temp_c is None:
        return 0
    # Kurve von hinten abarbeiten: erste Schwelle, die unterschritten wird
    target = FAN_CURVE[0][1]
    for threshold, percent in FAN_CURVE:
        if temp_c >= threshold:
            target = percent
    # Interpolation zwischen den Stufen für sanftes Hochlaufen
    for (t_lo, p_lo), (t_hi, p_hi) in zip(FAN_CURVE, FAN_CURVE[1:]):
        if t_lo <= temp_c < t_hi:
            share = (temp_c - t_lo) / (t_hi - t_lo)
            target = p_lo + (p_hi - p_lo) * share
            break
    # Hysterese: nur ändern, wenn der Unterschied sich lohnt
    if abs(target - current_percent) < HYSTERESIS:
        return current_percent
    return int(round(target))


class FanController:
    """Steuert den Lüfter per PWM. Auf dem Pi: echte PWM, sonst: Log-Ausgabe."""

    def __init__(self, pin=PWM_PIN, frequency=PWM_FREQUENCY, simulate=False):
        self.pin = pin
        self.frequency = frequency
        self.simulate = simulate
        self.percent = 0
        self._pwm = None

        if not simulate:
            try:
                from gpiozero import PWMOutputDevice
                # gpiozero nutzt hardwaretaugliche Software-PWM (pigpio falls installiert)
                self._pwm = PWMOutputDevice(pin, frequency=frequency, initial_value=0)
                self.hw = True
            except Exception as e:
                print("[Fan] gpiozero nicht verfügbar (%s) -> Nur-Simulations-Modus." % e)
                self.simulate = True
                self.hw = False
        else:
            self.hw = False

    def set_percent(self, percent):
        """Lüfter auf 0..100 % setzen."""
        self.percent = max(0, min(100, int(percent)))
        if self.hw and self._pwm is not None:
            self._pwm.value = self.percent / 100.0
        return self.percent

    def status(self):
        return {"pwm_pin": self.pin, "frequenz_hz": self.frequency,
                "drehzahl_prozent": self.percent, "hardware": self.hw}

    def close(self):
        if self._pwm is not None:
            self._pwm.close()
            self._pwm = None


def regulate_fan(fan, temp_c, current_percent):
    """Ein Regel-Schritt: Temperatur -> neue PWM. Gibt (percent, neu) zurück."""
    target = pwm_percent_for_temp(temp_c, current_percent)
    if target != current_percent:
        fan.set_percent(target)
    return fan.percent, target != current_percent


def vcgencmd_throttle_info():
    """Optional: Warum drosselt der Pi? (nur auf echtem Pi verfügbar)"""
    try:
        out = subprocess.check_output(["vcgencmd", "get_throttled"], timeout=1).decode()
        return out.strip()
    except Exception:
        return None


# ---------------- Selbsttest ----------------
if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Schritt 4: Sensoren & Lüfter testen")
    ap.add_argument("--simulate", action="store_true", help="Kein GPIO, nur anzeigen")
    ap.add_argument("--test", action="store_true", help="Kurztest und Ende")
    args = ap.parse_args()

    simulate = args.simulate or args.test
    fan = FanController(simulate=simulate)
    print("Lüfter-Regelung läuft. Strg+C beendet.")
    try:
        while True:
            temp = read_cpu_temp()
            percent, changed = regulate_fan(fan, temp, fan.percent)
            throttle = vcgencmd_throttle_info()
            print("Temp: %-6s | Lüfter: %3d %% %s | PWM-Pin: GPIO%d %s" % (
                ("%.1f C" % temp) if temp is not None else "--",
                percent,
                "(geändert)" if changed else "         ",
                fan.pin,
                ("| %s" % throttle) if throttle else ""))
            if args.test:
                break
            time.sleep(2)
    except KeyboardInterrupt:
        pass
    finally:
        fan.set_percent(0)
        fan.close()
        print("Lüfter aus, GPIO freigegeben.")
