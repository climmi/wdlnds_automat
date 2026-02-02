from typing import Optional


class PayoutController:
    def __init__(self) -> None:
        self._pending: Optional[str] = None

    def request(self, sticker_id: str) -> None:
        self._pending = sticker_id

    def clear(self) -> None:
        self._pending = None

    def pending(self) -> Optional[str]:
        return self._pending

    def dispense(self) -> bool:
        if self._pending is None:
            return False
        # Placeholder for real motor control logic.
        self._pending = None
        return True
