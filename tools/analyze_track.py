#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
import struct
import subprocess
from statistics import median


SAMPLE_RATE = 22050
HOP_SIZE = 512
FRAME_SIZE = 1024
DEFAULT_MIN_DURATION = 180.0
DEFAULT_MAX_DURATION = 300.0
CONTROL_ORDER = ("left", "middle", "right")


def remove_hold_lane_conflicts(cues: list[dict]) -> list[dict]:
    cleaned = []
    hold_windows: dict[str, list[tuple[float, float]]] = {control: [] for control in CONTROL_ORDER}
    margin = 0.05

    for cue in sorted(cues, key=lambda item: item["time"]):
        cue_time = float(cue["time"])
        controls = [control for control in cue.get("controls", [cue.get("control")]) if control in CONTROL_ORDER]
        if not controls:
            continue

        blocked = {
            control
            for control in controls
            for start, end in hold_windows.get(control, [])
            if start - margin < cue_time < end + margin
        }

        if cue.get("type") == "hold":
            if blocked:
                continue
            duration = float(cue.get("duration", 0.0) or 0.0)
            for control in controls:
                hold_windows[control].append((cue_time, cue_time + duration))
            cleaned.append(cue)
            continue

        controls = [control for control in controls if control not in blocked]
        if not controls:
            continue
        cue["controls"] = controls
        cue["control"] = controls[0]
        cleaned.append(cue)

    return cleaned


def decode_audio(path: str) -> list[int]:
    command = [
        "ffmpeg",
        "-v",
        "error",
        "-i",
        path,
        "-ac",
        "1",
        "-ar",
        str(SAMPLE_RATE),
        "-f",
        "s16le",
        "-",
    ]
    result = subprocess.run(command, check=True, stdout=subprocess.PIPE)
    count = len(result.stdout) // 2
    return list(struct.unpack(f"<{count}h", result.stdout))


def moving_average(values: list[float], radius: int) -> list[float]:
    if not values:
        return []
    smoothed = []
    total = 0.0
    queue = []
    width = radius * 2 + 1
    padded = [values[0]] * radius + values + [values[-1]] * radius
    for value in padded:
        queue.append(value)
        total += value
        if len(queue) > width:
            total -= queue.pop(0)
        if len(queue) == width:
            smoothed.append(total / width)
    return smoothed


def energy_envelope(samples: list[int]) -> tuple[list[float], list[float]]:
    energies = []
    times = []
    for start in range(0, max(0, len(samples) - FRAME_SIZE), HOP_SIZE):
        frame = samples[start:start + FRAME_SIZE]
        total = 0.0
        for sample in frame:
            normalized = sample / 32768.0
            total += normalized * normalized
        energies.append(math.sqrt(total / len(frame)))
        times.append((start + FRAME_SIZE / 2) / SAMPLE_RATE)
    return energies, times


def onset_envelope(energies: list[float]) -> list[float]:
    baseline = moving_average(energies, 12)
    flux = []
    previous = energies[0] if energies else 0.0
    for energy, base in zip(energies, baseline):
        lift = max(0.0, energy - previous, energy - base * 1.08)
        flux.append(lift)
        previous = energy
    peak = max(flux) if flux else 1.0
    if peak <= 0:
        return flux
    return [value / peak for value in flux]


def goertzel_power(frame: list[int], freq: float) -> float:
    coeff = 2.0 * math.cos(2.0 * math.pi * freq / SAMPLE_RATE)
    s_prev = 0.0
    s_prev2 = 0.0
    for sample in frame:
        value = sample / 32768.0
        s = value + coeff * s_prev - s_prev2
        s_prev2 = s_prev
        s_prev = s
    return s_prev2 * s_prev2 + s_prev * s_prev - coeff * s_prev * s_prev2


def band_envelopes(samples: list[int]) -> dict[str, list[float]]:
    bands = {
        "low": [70.0, 100.0, 140.0],
        "mid": [260.0, 420.0, 680.0],
        "high": [1100.0, 1800.0, 2800.0],
    }
    envelopes = {name: [] for name in bands}
    for start in range(0, max(0, len(samples) - FRAME_SIZE), HOP_SIZE):
        frame = samples[start:start + FRAME_SIZE]
        windowed = []
        for idx, sample in enumerate(frame):
            window = 0.5 - 0.5 * math.cos((2.0 * math.pi * idx) / max(1, len(frame) - 1))
            windowed.append(int(sample * window))
        for name, freqs in bands.items():
            envelopes[name].append(sum(goertzel_power(windowed, freq) for freq in freqs))

    for name, values in envelopes.items():
        peak = max(values) if values else 1.0
        if peak > 0:
            envelopes[name] = [value / peak for value in values]
    return envelopes


def estimate_tempo(onsets: list[float]) -> float:
    if not onsets:
        return 120.0
    best_bpm = 120.0
    best_score = -1.0
    for bpm in range(82, 176):
        lag = int(round((60.0 / bpm) * SAMPLE_RATE / HOP_SIZE))
        if lag <= 0 or lag >= len(onsets):
            continue
        score = 0.0
        for idx in range(lag, len(onsets)):
            score += onsets[idx] * onsets[idx - lag]
        score /= max(1, len(onsets) - lag)
        if score > best_score:
            best_score = score
            best_bpm = float(bpm)
    return best_bpm


def pick_peaks(onsets: list[float], times: list[float], bpm: float) -> list[dict]:
    if not onsets:
        return []
    threshold = max(0.10, median(onsets) * 2.6)
    min_gap = max(0.18, (60.0 / bpm) * 0.48)
    peaks = []
    last_time = -999.0
    for idx in range(1, len(onsets) - 1):
        value = onsets[idx]
        if value < threshold:
            continue
        if value < onsets[idx - 1] or value < onsets[idx + 1]:
            continue
        time = times[idx]
        if time - last_time < min_gap:
            if peaks and value > peaks[-1]["strength"]:
                peaks[-1] = {"time": time, "strength": value}
                last_time = time
            continue
        peaks.append({"time": time, "strength": value})
        last_time = time
    return peaks


def estimate_beat_phase(peaks: list[dict], bpm: float, duration: float) -> float:
    beat = 60.0 / bpm
    best_phase = 0.0
    best_score = -1.0
    candidates = 32
    strong_peaks = [peak for peak in peaks if 0.5 <= peak["time"] <= min(duration, 120.0)]
    for step in range(candidates):
        phase = beat * (step / candidates)
        score = 0.0
        for peak in strong_peaks:
            pos = (peak["time"] - phase) / beat
            distance = abs(pos - round(pos))
            distance = min(distance, 1.0 - distance)
            score += peak["strength"] * max(0.0, 1.0 - distance * 6.0)
        if score > best_score:
            best_score = score
            best_phase = phase
    return best_phase


def quantize_time(time: float, phase: float, step: float) -> float:
    return phase + round((time - phase) / step) * step


def segment_for_time(time: float, duration: float) -> tuple[str, str]:
    if time < 10.0:
        return "ANKOMMEN", "intro"
    if time < 30.0:
        return "EINFACH", "easy"
    if time < min(duration, 105.0):
        return "GROOVE", "medium"
    if time < min(duration, 190.0):
        return "DROP", "hard"
    return "FINALE", "hard"


def build_cues(peaks: list[dict], bpm: float, duration: float, bands: dict[str, list[float]], max_duration: float) -> dict:
    beat = 60.0 / bpm
    chart_duration = min(duration, max_duration)
    phase = estimate_beat_phase(peaks, bpm, chart_duration)
    cues = []
    last_controls = []
    occupied: dict[float, set[str]] = {}
    for idx, peak in enumerate(peaks):
        time = peak["time"]
        if time < 1.0 or time > chart_duration - 0.5:
            continue
        beat_index = int(round(time / beat))
        _, difficulty = segment_for_time(time, chart_duration)
        if difficulty == "intro":
            grid = beat * 2.0
            min_strength = 0.08
        elif difficulty == "easy":
            grid = beat
            min_strength = 0.12
        elif difficulty == "medium":
            grid = beat / 2.0
            min_strength = 0.16
        else:
            grid = beat / 2.0
            min_strength = 0.13
        if peak["strength"] < min_strength:
            continue

        cue_time = quantize_time(time, phase, grid)
        if cue_time < 1.0 or cue_time > chart_duration - 0.5:
            continue
        frame_idx = max(0, min(len(bands["low"]) - 1, int(round(time * SAMPLE_RATE / HOP_SIZE))))
        band_values = {
            "left": bands["low"][frame_idx],
            "middle": bands["mid"][frame_idx],
            "right": bands["high"][frame_idx],
        }
        ranked = sorted(band_values.items(), key=lambda item: item[1], reverse=True)

        if difficulty == "intro":
            if beat_index % 4 not in (0, 2):
                continue
            controls = [ranked[0][0]]
            cue_type = "tap"
        elif difficulty == "easy":
            if beat_index % 2 == 1 and peak["strength"] < 0.42:
                continue
            controls = [ranked[0][0]]
            cue_type = "tap"
        elif difficulty == "medium":
            controls = [ranked[0][0]]
            cue_type = "hold" if peak["strength"] > 0.58 and beat_index % 8 == 0 else "tap"
        else:
            controls = [ranked[0][0]]
            second_is_clear = ranked[1][1] > 0.46 and ranked[1][1] > ranked[0][1] * 0.72
            downbeat = beat_index % 8 == 0
            hard_downbeat = beat_index % 16 in (0, 8)
            if (peak["strength"] > 0.56 and (second_is_clear or downbeat)) or (
                peak["strength"] > 0.38 and hard_downbeat
            ):
                controls.append(ranked[1][0])
            cue_type = "hold" if len(controls) == 1 and peak["strength"] > 0.72 and beat_index % 8 in (0, 4) else "tap"

        if controls == last_controls and time < 30.0:
            controls = [ranked[1][0] if ranked[1][0] != controls[0] else ranked[0][0]]
        last_controls = list(controls)

        controls = controls[:2]
        occupied_controls = occupied.setdefault(round(cue_time, 3), set())
        if difficulty in ("intro", "easy") and occupied_controls:
            continue
        controls = [control for control in controls if control not in occupied_controls]
        if not controls:
            continue
        if len(occupied_controls) + len(controls) > 2:
            controls = controls[:max(0, 2 - len(occupied_controls))]
        if not controls:
            continue
        occupied_controls.update(controls)

        hold_duration = 0.0
        if cue_type == "hold":
            hold_duration = beat * (2.0 if difficulty == "medium" else 3.0)
            hold_duration = min(hold_duration, chart_duration - cue_time - 0.5)
            if hold_duration < beat * 1.2:
                cue_type = "tap"
                hold_duration = 0.0

        cues.append({
            "time": round(cue_time, 3),
            "control": controls[0],
            "controls": controls,
            "type": cue_type,
            "duration": round(hold_duration, 3),
            "strength": round(peak["strength"], 3),
            "bands": {key: round(value, 3) for key, value in band_values.items()},
        })

    cues.sort(key=lambda item: item["time"])
    cues = remove_hold_lane_conflicts(cues)

    sections = []
    boundaries = [
        (0.0, min(10.0, chart_duration), "ANKOMMEN", "intro"),
        (10.0, min(30.0, chart_duration), "EINFACH", "easy"),
        (30.0, min(105.0, chart_duration), "GROOVE", "medium"),
        (105.0, min(190.0, chart_duration), "DROP", "hard"),
        (190.0, chart_duration, "FINALE", "hard"),
    ]
    for start, end, name, difficulty in boundaries:
        if end <= start:
            continue
        sections.append([round(start, 3), round(end, 3), name, difficulty])

    return {
        "source": "",
        "sample_rate": SAMPLE_RATE,
        "bpm": round(bpm, 2),
        "beat_phase": round(phase, 3),
        "duration": round(chart_duration, 3),
        "cues": cues,
        "sections": sections,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze an audio file and write Show Control cue timings.")
    parser.add_argument("audio_path")
    parser.add_argument("--output", default=os.path.join("data", "show_cues.json"))
    parser.add_argument("--min-duration", type=float, default=DEFAULT_MIN_DURATION)
    parser.add_argument("--max-duration", type=float, default=240.0)
    args = parser.parse_args()

    samples = decode_audio(args.audio_path)
    duration = len(samples) / SAMPLE_RATE
    energies, times = energy_envelope(samples)
    onsets = onset_envelope(energies)
    bands = band_envelopes(samples)
    bpm = estimate_tempo(onsets)
    peaks = pick_peaks(onsets, times, bpm)
    chart_duration = min(duration, max(args.min_duration, args.max_duration))
    payload = build_cues(peaks, bpm, chart_duration, bands, args.max_duration)
    payload["source"] = os.path.basename(args.audio_path)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)

    print(f"source: {payload['source']}")
    print(f"duration: {payload['duration']}s")
    print(f"bpm: {payload['bpm']}")
    print(f"cues: {len(payload['cues'])}")
    print(f"output: {args.output}")


if __name__ == "__main__":
    main()
