from machine import ADC, Pin
import neopixel
import select
import sys
import time


LED_PIN = 19
LED_COUNT = 172
LED_BRIGHTNESS = 48

BUTTONS = {
    "left": 25,
    "middle": 26,
    "right": 27,
    "start": 14,
}

BUTTON_LEDS = {
    "right": 0,
    "middle": 1,
    "left": 2,
    "start": 3,
}

COIN_ADC_PIN = 34
DEBOUNCE_MS = 28
COIN_COOLDOWN_MS = 650
COIN_DROP_RATIO = 0.82
COIN_RESET_RATIO = 0.92

COLORS = {
    "left": (50, 115, 255),
    "middle": (255, 174, 40),
    "right": (235, 85, 70),
    "start": (255, 240, 120),
    "idle": (18, 12, 6),
    "coin": (80, 255, 120),
}


def scale(color, brightness=LED_BRIGHTNESS):
    return tuple(min(255, max(0, int(channel * brightness / 255))) for channel in color)


def logical_range(start, end):
    first = max(0, start + 3)
    last = min(LED_COUNT - 1, end + 3)
    return list(range(first, last + 1)) if first <= last else []


FIELDS = {
    "teil_left": logical_range(1, 2),
    "volle_left": logical_range(3, 4),
    "venus_multi_55_middle": logical_range(5, 22),
    "multi_middle": logical_range(23, 24),
    "serie_middle": logical_range(25, 26),
    "40_middle_top": logical_range(27, 28),
    "50_middle_top": logical_range(29, 30),
    "30_middle_top": logical_range(31, 32),
    "sun_4_middle": logical_range(33, 35),
    "sun_3_middle": logical_range(36, 38),
    "coins_3_middle": logical_range(39, 41),
    "coins_2_middle": logical_range(42, 44),
    "gestoert_left": logical_range(45, 46),
    "start_left": logical_range(47, 52),
    "50_left": logical_range(53, 54),
    "25_left": logical_range(55, 56),
    "12_left": logical_range(57, 58),
    "6_left": logical_range(59, 60),
    "3_left": logical_range(61, 62),
    "260_left": logical_range(63, 64),
    "130_left": logical_range(65, 66),
    "060_left": logical_range(67, 68),
    "030_left": logical_range(69, 70),
    "0_left": logical_range(71, 72),
    "start_auto_middle": logical_range(73, 74),
    "0_middle": logical_range(75, 76),
    "20_middle": logical_range(77, 83),
    "40_middle": logical_range(84, 90),
    "70_middle": logical_range(91, 97),
    "150_middle": logical_range(98, 104),
    "3_middle": logical_range(105, 115),
    "4_middle": logical_range(116, 126),
    "ausspielung_middle": logical_range(127, 141),
    "0_right": logical_range(142, 143),
    "20_right_bottom": logical_range(144, 145),
    "40_right_bottom": logical_range(146, 147),
    "80_right": logical_range(148, 149),
    "160_right": logical_range(150, 151),
    "2_right": logical_range(152, 155),
    "stop_right": logical_range(156, 161),
    "4_right": logical_range(162, 163),
    "10_right": logical_range(164, 165),
    "20_right_top": logical_range(166, 167),
    "40_right_top": logical_range(168, 169),
}

LANE_SEGMENTS = {
    "left": [
        FIELDS["teil_left"], FIELDS["volle_left"], FIELDS["gestoert_left"],
        FIELDS["start_left"], FIELDS["50_left"], FIELDS["25_left"], FIELDS["12_left"],
        FIELDS["6_left"], FIELDS["3_left"], FIELDS["260_left"], FIELDS["130_left"],
        FIELDS["060_left"], FIELDS["030_left"], FIELDS["0_left"],
    ],
    "middle": [
        FIELDS["venus_multi_55_middle"], FIELDS["multi_middle"], FIELDS["serie_middle"],
        FIELDS["40_middle_top"], FIELDS["50_middle_top"], FIELDS["30_middle_top"],
        FIELDS["sun_4_middle"], FIELDS["sun_3_middle"], FIELDS["coins_3_middle"],
        FIELDS["coins_2_middle"], FIELDS["start_auto_middle"], FIELDS["0_middle"],
        FIELDS["20_middle"], FIELDS["40_middle"], FIELDS["70_middle"], FIELDS["150_middle"],
        FIELDS["3_middle"], FIELDS["4_middle"], FIELDS["ausspielung_middle"],
    ],
    "right": [
        FIELDS["40_right_top"], FIELDS["20_right_top"], FIELDS["10_right"], FIELDS["4_right"],
        FIELDS["stop_right"], FIELDS["2_right"], FIELDS["160_right"], FIELDS["80_right"],
        FIELDS["40_right_bottom"], FIELDS["20_right_bottom"], FIELDS["0_right"],
    ],
}

STANDBY_FIELDS = [
    ("left", FIELDS["teil_left"] + FIELDS["volle_left"]),
    ("middle", FIELDS["venus_multi_55_middle"]),
    ("right", FIELDS["40_right_top"] + FIELDS["20_right_top"]),
    ("middle", FIELDS["sun_4_middle"] + FIELDS["sun_3_middle"]),
    ("left", FIELDS["start_left"]),
    ("middle", FIELDS["ausspielung_middle"]),
    ("right", FIELDS["stop_right"]),
    ("left", FIELDS["0_left"] + FIELDS["030_left"]),
    ("middle", FIELDS["3_middle"] + FIELDS["4_middle"]),
    ("right", FIELDS["2_right"] + FIELDS["160_right"]),
]


class DebouncedButton:
    def __init__(self, name, pin):
        self.name = name
        self.pin = Pin(pin, Pin.IN, Pin.PULL_UP)
        self.stable = self.pin.value()
        self.last_raw = self.stable
        self.last_change = time.ticks_ms()

    def update(self):
        raw = self.pin.value()
        now = time.ticks_ms()
        if raw != self.last_raw:
            self.last_raw = raw
            self.last_change = now
            return None
        if raw != self.stable and time.ticks_diff(now, self.last_change) >= DEBOUNCE_MS:
            self.stable = raw
            return "down" if raw == 0 else "up"
        return None


class CoinGate:
    def __init__(self):
        self.adc = ADC(Pin(COIN_ADC_PIN))
        self.adc.atten(ADC.ATTN_11DB)
        self.baseline = self._calibrate()
        self.blocked = False
        self.last_coin = 0

    def _calibrate(self):
        total = 0
        for _ in range(80):
            total += self.adc.read()
            time.sleep_ms(8)
        return max(1, total // 80)

    def update(self):
        value = self.adc.read()
        now = time.ticks_ms()

        if not self.blocked:
            self.baseline = max(1, int(self.baseline * 0.995 + value * 0.005))
            if value < self.baseline * COIN_DROP_RATIO and time.ticks_diff(now, self.last_coin) > COIN_COOLDOWN_MS:
                self.blocked = True
                self.last_coin = now
                return True
        elif value > self.baseline * COIN_RESET_RATIO:
            self.blocked = False

        return False


class Strip:
    def __init__(self):
        self.pixels = neopixel.NeoPixel(Pin(LED_PIN, Pin.OUT), LED_COUNT)
        self.mode = "standby"
        self.mood = 35
        self.flash_until = 0
        self.flash_color = COLORS["idle"]
        self.lanes = {name: [0, 0] for name in ("left", "middle", "right")}
        self.prompts = {name: 0 for name in ("left", "middle", "right", "start")}
        self.last_frame = 0
        self.boot()

    def boot(self):
        for i in range(LED_COUNT):
            if i in BUTTON_LEDS.values():
                self.pixels[i] = scale(COLORS["start"], 70)
            elif i % 3 == 0:
                self.pixels[i] = scale(COLORS["left"], 32)
            elif i % 3 == 1:
                self.pixels[i] = scale(COLORS["middle"], 32)
            else:
                self.pixels[i] = scale(COLORS["right"], 32)
        self.pixels.write()
        time.sleep_ms(220)
        self.clear()

    def set_mode(self, mode):
        if mode not in ("standby", "game"):
            return
        if self.mode != mode:
            self.mode = mode
            self.clear()

    def clear(self):
        self._fill(scale(COLORS["idle"], 9))

    def flash(self, name):
        self.flash_color = COLORS.get(name, COLORS["coin"])
        self.flash_until = time.ticks_add(time.ticks_ms(), 160)
        self._fill(scale(self.flash_color, LED_BRIGHTNESS))

    def mood_set(self, value):
        self.mood = max(0, min(100, int(value)))

    def set_lane(self, lane, position, intensity):
        if lane in self.lanes:
            self.lanes[lane] = [max(0, min(100, int(position))), max(0, min(255, int(intensity)))]

    def set_prompt(self, lane, intensity):
        if lane in self.prompts:
            self.prompts[lane] = max(0, min(255, int(intensity)))

    def set_game(self, parts):
        if len(parts) < 10:
            return
        lanes = ("left", "middle", "right")
        for i, lane in enumerate(lanes):
            offset = i * 3
            self.set_lane(lane, parts[offset], parts[offset + 1])
            self.set_prompt(lane, parts[offset + 2])
        self.mood_set(parts[9])

    def update(self):
        now = time.ticks_ms()
        if self.flash_until and time.ticks_diff(now, self.flash_until) <= 0:
            return
        if self.flash_until:
            self.flash_until = 0

        if time.ticks_diff(now, self.last_frame) < 42:
            return
        self.last_frame = now

        if self.mode == "game":
            self._draw_game(now)
        else:
            self._draw_standby(now)

    def _draw_standby(self, now):
        self._fill_no_write(scale(COLORS["idle"], 10 + int(self.mood * 0.08)))
        step = (now // 150) % len(STANDBY_FIELDS)
        for offset in range(3):
            lane, pixels = STANDBY_FIELDS[(step + offset) % len(STANDBY_FIELDS)]
            brightness = (90, 48, 24)[offset]
            self._set_pixels(pixels, scale(COLORS[lane], brightness))

        pulse = 36 + ((now // 18) % 38)
        self._set_button("start", scale(COLORS["start"], pulse))
        self.pixels.write()

    def _draw_game(self, now):
        self._fill_no_write(scale(COLORS["idle"], 6))
        for lane, payload in self.lanes.items():
            position, intensity = payload
            if intensity > 0:
                self._draw_lane(lane, position, intensity)
            self.lanes[lane][1] = max(0, intensity - 34)

        for lane, intensity in self.prompts.items():
            if intensity > 0:
                color = COLORS.get(lane, COLORS["start"])
                self._set_button(lane, scale(color, min(255, intensity)))
                if lane in LANE_SEGMENTS:
                    for segment in LANE_SEGMENTS[lane]:
                        self._set_pixels(segment, scale(color, min(150, max(40, intensity // 2))))
                self.prompts[lane] = max(0, intensity - 28)

        self.pixels.write()

    def _draw_lane(self, lane, position, intensity):
        segments = LANE_SEGMENTS.get(lane, [])
        if not segments:
            return
        color = COLORS[lane]
        index = min(len(segments) - 1, max(0, int(position * len(segments) / 101)))
        for trail in range(3):
            seg_index = index - trail
            if seg_index < 0:
                continue
            brightness = max(16, intensity - trail * 54)
            self._set_pixels(segments[seg_index], scale(color, brightness))

    def _set_button(self, name, color):
        index = BUTTON_LEDS.get(name)
        if index is not None and 0 <= index < LED_COUNT:
            self.pixels[index] = color

    def _set_pixels(self, pixels, color):
        for index in pixels:
            if 0 <= index < LED_COUNT:
                self.pixels[index] = color

    def _fill(self, color):
        self._fill_no_write(color)
        self.pixels.write()

    def _fill_no_write(self, color):
        for i in range(LED_COUNT):
            self.pixels[i] = color


def handle_command(line, strip):
    parts = line.strip().split()
    if not parts:
        return
    if parts[0] == "MODE" and len(parts) >= 2:
        strip.set_mode(parts[1])
    elif parts[0] == "LANE" and len(parts) >= 4:
        strip.set_lane(parts[1], parts[2], parts[3])
    elif parts[0] == "PROMPT" and len(parts) >= 3:
        strip.set_prompt(parts[1], parts[2])
    elif parts[0] == "GAME" and len(parts) >= 11:
        strip.set_game(parts[1:11])
    elif parts[0] == "LED" and len(parts) >= 2:
        if parts[1] == "off":
            strip._fill((0, 0, 0))
        elif parts[1] in ("idle", "standby"):
            strip.set_mode("standby")
        elif parts[1] == "flash" and len(parts) >= 3:
            if parts[2] in ("left", "middle", "right", "start"):
                strip.set_prompt(parts[2], 255)
            else:
                strip.flash(parts[2])
    elif parts[0] == "MOOD" and len(parts) >= 2:
        strip.mood_set(parts[1])


def main():
    buttons = [DebouncedButton(name, pin) for name, pin in BUTTONS.items()]
    coin = CoinGate()
    strip = Strip()
    poll = select.poll()
    poll.register(sys.stdin, select.POLLIN)

    print("READY esp32_io")
    print("LDR baseline {}".format(coin.baseline))

    while True:
        for button in buttons:
            event = button.update()
            if event:
                print("BTN {} {}".format(button.name, event))
                if event == "down":
                    strip.set_prompt(button.name, 255)

        if coin.update():
            print("COIN")
            strip.flash("coin")

        for _ in range(8):
            if not poll.poll(0):
                break
            handle_command(sys.stdin.readline(), strip)

        strip.update()
        time.sleep_ms(5)


main()
