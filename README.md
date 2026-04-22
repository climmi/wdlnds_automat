# Woodlands Automat (Prototype)

Leichtgewichtiges Pygame-UI fuer den umgebauten Gluecksspielautomaten.

## Projektueberblick

- `app/main.py` startet das Spiel und bindet Eingaben, Credits und State-Machine zusammen.
- `app/states/` enthaelt die Spielscreens und Minigames.
- `app/hardware/` kapselt GPIO, Buttons, Coin-Sensor, Lampen, Sound und Sticker-Auswurf.
- Auf Nicht-Pi-Systemen faellt das Projekt automatisch auf Tastatursteuerung zurueck.

## Mac-Setup

Voraussetzungen:

- `python3` installiert
- auf dem Mac fuer die lokale Entwicklung nur `pygame`

Empfohlener Start:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m app.main
```

Optional:

```bash
python -m app.main --width 1024 --height 576 --fullscreen
```

Wenn `pygame` auf dem Mac beim Installieren zickt, pruefe zuerst deine Python-Version. Im aktuellen Projekt liegt lokal `Python 3.9.6` vor, das ist fuer dieses Repo grundsaetzlich okay.

## Raspberry-Pi-Setup

Auf dem Pi brauchst du zusaetzlich die GPIO-Bibliotheken:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install -r requirements-pi.txt
```

Die GPIO-Zuordnung ist aktuell zentral in `App._attach_gpio_inputs()` in `app/main.py` hinterlegt:

- `left` = GPIO17
- `middle` = GPIO27
- `right` = GPIO22
- `start` = GPIO23
- `coin` = GPIO24

Die Logik benutzt `gpiozero` mit bevorzugtem `lgpio`-Backend. Wenn das auf dem Mac oder einem Nicht-Pi-System fehlt, bleibt die Tastatursteuerung aktiv.

## Start

```bash
python -m app.main
```

Optional:

```bash
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

Die Klassen in `app/hardware` sind vorbereitet fuer GPIO. Die aktuelle Pin-Zuordnung passiert zentral in `App._attach_gpio_inputs()`.

## Sticker-Auswurf

Der `PayoutController` ist aktuell nur eine Schnittstelle. Hier kann spaeter die Motorsteuerung ergaenzt werden.

## Pixel-Fonts (optional)

Lege die TTF-Dateien in `app/assets/fonts/` ab:
- `PressStart2P-Regular.ttf`
- `VT323-Regular.ttf`

Die App nutzt diese automatisch, sonst faellt sie auf System-Fonts zurueck.

## WebP -> PNG Konverter

Wenn du WebP-Dateien hast, kannst du sie so konvertieren:

```bash
python tools/convert_webp_to_png.py
```

Dafuer wird `Pillow` benoetigt:

```bash
python -m pip install pillow
```

## Pi-Deploy von macOS oder Linux

Lokal testen:

```bash
python -m app.main
```

Deploy auf den Raspberry Pi (Upload + Install + Service-Restart):

```bash
chmod +x tools/deploy_pi.sh
./tools/deploy_pi.sh
```

Wenn du in `~/.ssh/config` den Host `wdlnds-pi` angelegt hast, nutzt das Skript diesen Namen automatisch als Standard.
Dann brauchst du meistens keinen `--host`-Parameter mehr.

Optionen:

```bash
# Nur Upload, kein pip install
./tools/deploy_pi.sh --skip-install

# Upload + Install, aber ohne Service-Neustart
./tools/deploy_pi.sh --no-restart

# Host/User ueberschreiben (falls noetig)
./tools/deploy_pi.sh --host wdlnds-pi --user qwert
```

Die bisherige Windows-Variante bleibt weiter in `tools/deploy_pi.ps1`, falls du sie irgendwann noch brauchst.
