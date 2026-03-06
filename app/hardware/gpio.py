import sys

GPIO_INIT_ERROR = None

try:
    from gpiozero import Button, Device  # type: ignore
    try:
        # Prefer lgpio backend on modern Raspberry Pi OS builds.
        from gpiozero.pins.lgpio import LGPIOFactory  # type: ignore
        Device.pin_factory = LGPIOFactory()
    except Exception as exc:  # pragma: no cover - backend fallback
        GPIO_INIT_ERROR = f"LGPIOFactory not active: {exc}"
except Exception as exc:  # pragma: no cover - fallback on non-Pi systems
    Button = None
    GPIO_INIT_ERROR = f"gpiozero import failed: {exc}"


class GpioButton:
    def __init__(self, pin: int, pull_up: bool = True) -> None:
        if Button is None:
            self._button = None
            if GPIO_INIT_ERROR:
                print(GPIO_INIT_ERROR, file=sys.stderr)
            return
        try:
            self._button = Button(pin, pull_up=pull_up, bounce_time=0.02)
        except Exception as exc:
            self._button = None
            print(f"GPIO button init failed on pin {pin}: {exc}", file=sys.stderr)

    def is_pressed(self) -> bool:
        if self._button is None:
            return False
        return bool(self._button.is_pressed)
