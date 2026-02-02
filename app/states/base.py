class BaseState:
    def __init__(self, app) -> None:
        self.app = app

    def on_enter(self) -> None:
        pass

    def on_exit(self) -> None:
        pass

    def handle_input(self, pressed):
        pass

    def update(self, dt: float) -> None:
        pass

    def render(self, surface) -> None:
        pass
