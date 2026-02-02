class StateMachine:
    def __init__(self, states, initial: str) -> None:
        self._states = states
        self._current = self._states[initial]
        self._current.on_enter()

    def change(self, name: str) -> None:
        if name not in self._states:
            raise KeyError(f"Unknown state: {name}")
        self._current.on_exit()
        self._current = self._states[name]
        self._current.on_enter()

    def handle_input(self, pressed) -> None:
        self._current.handle_input(pressed)

    def update(self, dt: float) -> None:
        self._current.update(dt)

    def render(self, surface) -> None:
        self._current.render(surface)

    @property
    def current(self):
        return self._current
