try:
    from gpiozero import Button  # type: ignore
except Exception:  # pragma: no cover - fallback on non-Pi systems
    Button = None


class GpioButton:
    def __init__(self, pin: int, pull_up: bool = True) -> None:
        if Button is None:
            self._button = None
            return
        self._button = Button(pin, pull_up=pull_up, bounce_time=0.02)

    def is_pressed(self) -> bool:
        if self._button is None:
            return False
        return bool(self._button.is_pressed)
