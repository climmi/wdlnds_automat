# Woodlands Automat (Prototype)

Leichtgewichtiges Pygame-UI fuer den umgebauten Gluecksspielautomaten.

## Start

```powershell
python -m app.main
```

Optional:

```powershell
python -m app.main --width 1024 --height 576 --fullscreen
```

## Steuerung (Tastatur-Simulation)

- Linke Taste: `A` oder Pfeil links
- Mittlere Taste: `S` oder Pfeil unten
- Rechte Taste: `D` oder Pfeil rechts
- Start/OK: `Enter` oder `Space`
- Pfandmarke (Coin): `C`

Im Game-Over-Screen:
- Links/Rechts: Zeichen wechseln
- Mitte: Feld wechseln
- Start: bestaetigen

## GPIO-Pins (Platzhalter)

Die Klassen in `app/hardware` sind vorbereitet fuer GPIO. Du kannst in `ButtonManager.attach_gpio(...)` und `CoinSensor.attach_gpio(...)` die Pins hinterlegen.

## Sticker-Auswurf

Der `PayoutController` ist aktuell nur eine Schnittstelle. Hier kann spaeter die Motorsteuerung ergaenzt werden.

## Pixel-Fonts (optional)

Lege die TTF-Dateien in `app/assets/fonts/` ab:
- `PressStart2P-Regular.ttf`
- `VT323-Regular.ttf`

Die App nutzt diese automatisch, sonst faellt sie auf System-Fonts zurueck.

## WebP -> PNG Konverter

Wenn du WebP-Dateien hast, kannst du sie so konvertieren:

```powershell
python tools/convert_webp_to_png.py
```

Dafuer wird `Pillow` benoetigt:

```powershell
python -m pip install pillow
```
## Highscore-Countdown (persistiert)

Der Countdown wird in `data/contest.json` mit Start- und Endzeit gespeichert. Wenn die App beendet oder neu gestartet wird, laeuft der Countdown weiter und wird beim Start wieder geladen.
