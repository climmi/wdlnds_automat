from signal import pause

from gpiozero import Button

PINS = {
    "left": 17,
    "middle": 27,
    "right": 22,
    "start": 23,
    "coin": 24,
}

buttons = {}
for name, pin in PINS.items():
    btn = Button(pin, pull_up=True, bounce_time=0.02)
    btn.when_pressed = lambda n=name: print(f"{n}: pressed", flush=True)
    btn.when_released = lambda n=name: print(f"{n}: released", flush=True)
    buttons[name] = btn

print("GPIO test ready. Press buttons (Ctrl+C to exit).", flush=True)
pause()
