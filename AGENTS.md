# Woodlands Automat Agent Onboarding

This file is the handoff note for AI agents working on this project. Read it before editing code.

## Current Project Path

Use this repo:

`/Users/climmichel/PROJECT CLIM/Projekte/woodlands e.V./wdlnds_automat`

There is an older path without `woodlands e.V.` in earlier chat history. Do not assume that older path is current.

## What The App Is

The app is a pygame-based Raspberry Pi arcade/coin machine for Woodlands. It runs fullscreen on the Pi, talks to an ESP32 over serial for buttons/coin/LEDs, plays music tracks, and shows a timing game based on DJ/show-control cues.

The current main flow is:

- `IdleState`: standby screen, waits for coin.
- `SongSelectState`: first chooses difficulty/location, then chooses one of the tracks for that location.
- `MiniGameState`: current main game, `game_id = "show_control"`.
- `ScoreGameState`: shared result/highscore/name-entry flow.

The active runtime in `app/main.py` only wires:

- `idle`
- `song_select`
- `minigame`

## Current Game Concept

The active game is a Woodlands DJ/show-control rhythm game. The player presses three buttons:

- left = `MOVE`
- middle = `DROP`
- right = `FX`

Cues fall toward target buttons. The player hits cues in time to keep the mood high, grow the crowd, and finish the track.

Tracks and cues are loaded from:

- `data/song_catalog.json`
- `data/cues/generated/*.json`
- `audio/songs_optimized/*.mp3`

Original imported songs live in `audio/songs/*`. Runtime uses optimized MP3 copies in `audio/songs_optimized/*` so the Pi has less decoding/file-size pressure.

Difficulty/location mapping should stay:

- easy = `Waldwinkel`
- medium = `ZOB`
- hard = `Marktplatz`

Level graphics live in:

- `graphic/level/Waldwinkel 01.png`
- `graphic/level/ZOB 01.png`
- `graphic/level/Marktplatz 01.png`

## Hardware

Raspberry Pi inputs:

- left = BCM GPIO17
- middle = BCM GPIO27
- right = BCM GPIO22
- start = BCM GPIO23
- coin = BCM GPIO24

ESP32 firmware:

- `firmware/esp32_io/main.py`
- serial default on Pi: `/dev/ttyUSB0`
- host controller: `app/hardware/esp32_serial.py`

The Pi sends LED/game state commands such as:

- `MODE standby`
- `MODE game`
- `LED flash left`
- `GAME <left position intensity prompt> <middle ...> <right ...> <mood>`

ESP32 sends input events back:

- `BTN left down`
- `BTN left up`
- `COIN`

If LEDs freeze, suspect ESP32 firmware crash/hang, serial disconnect, or command parsing errors. Prefer watchdogs, heartbeat, parse guards, and reconnect logic over visual-only fixes.

## Local Development

Start locally:

```bash
cd "/Users/climmichel/PROJECT CLIM/Projekte/woodlands e.V./wdlnds_automat"
source .venv/bin/activate
python -m app.main
```

Local keyboard fallback:

- `A` or left arrow = left
- `S` or down arrow = middle
- `D` or right arrow = right
- `Enter` or `Space` = start
- `C` = coin
- `Q` = debug overlay
- `Esc` = quit

Local dev shortcuts:

- `1` = song select
- `9` = set credits
- `0` = reset to idle

## Deploy

Deploy to Raspberry Pi:

```bash
./tools/deploy_pi.sh
```

Defaults:

- host = `wdlnds-pi`
- user = `qwert`
- remote dir = `/home/qwert/wdlnds_automat`
- service = `wdlnds-automat.service`

The deploy script zips the local project, uploads it, installs requirements, and restarts the service. It excludes the oversized source file `audio/soundeffects/standby_sound.opus`; runtime uses `audio/soundeffects/standby_sound_loop.mp3`.

ESP32 firmware is not updated by the deploy script. Use `mpremote` on the Pi when firmware changes:

```bash
sudo systemctl stop wdlnds-automat.service
cd /home/qwert/wdlnds_automat
.venv/bin/python -m mpremote connect /dev/ttyUSB0 fs cp firmware/esp32_io/main.py :main.py
.venv/bin/python -m mpremote connect /dev/ttyUSB0 reset
sudo systemctl start wdlnds-automat.service
```

## Current User Preferences

- Keep the gameplay header minimal.
- Do not show a large `DJ SET` title during gameplay.
- Show mood, streak, and track progress.
- Make cue feedback clear: early, late, good, perfect.
- Use separate scoreboards for Waldwinkel, ZOB, and Marktplatz.
- Keep Pi performance stable, especially with large crowds.
- Location selection should stay visually clean; do not show "3 tracks" on the location cards.

## Current Stabilization Notes

- Standby audio now uses a 90-second optimized loop file.
- Coin, combo, streak-break, scoreboard, and early-game-over sound effects are wired through `SoundManager`.
- The crowd renderer caches scaled sprites and caps drawn people per frame.
- Crowd character sets are loaded dynamically from `graphic/charakters/*`; each person can have individual `bored`, `normal`, and `happy` sprites plus different mood/combo thresholds.
- Character sprites are now loaded as exported, without runtime white-matte cleanup or normalization. If the people look wrong, fix the source exports instead of adding destructive runtime image processing.
- Crowd people are intentionally smaller and keep a fixed scale while entering; do not scale them up as the player hits more notes. Waldwinkel and ZOB mirror crowd sprites horizontally at runtime, Marktplatz keeps the original direction.
- Mood gain is streak-gated: low combos do not raise mood, longer streaks raise mood faster, and high mood has drag so 100% is harder to reach.
- Combo sound tiers trigger at streak totals 3, 8, 15, and 25.
- Cue controls are spaced and varied at runtime to avoid long single-lane runs from the analyzed cue data. Waldwinkel is thinned to simple taps, ZOB is medium-hard density with longer connected sequences, and Marktplatz keeps much denser/harder patterns without very short gaps.
- Pi-side ESP32 serial now has heartbeat/reconnect logic.
- ESP32 firmware now has watchdog, parser guards, `PING`/`PONG`, and a game-command timeout that falls back to standby.

## Editing Notes

- Use `apply_patch` for manual edits.
- Do not delete user assets casually. If optimizing a large asset, create an optimized runtime asset and keep the original out of deploy if needed.
- Keep generated caches and local venv out of git.
- Test with `py_compile` and a dummy SDL smoke test before deploy.
