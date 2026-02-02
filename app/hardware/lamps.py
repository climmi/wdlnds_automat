class LampController:
    def __init__(self) -> None:
        self._state = False

    def set_state(self, enabled: bool) -> None:
        self._state = bool(enabled)

    def is_on(self) -> bool:
        return self._state
