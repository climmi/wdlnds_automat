import os
import time


class Esp32SerialController:
    def __init__(self, port: str | None = None, baudrate: int = 115200) -> None:
        self.port = port or os.environ.get("WDLNDS_ESP32_PORT", "/dev/ttyUSB0")
        self.baudrate = baudrate
        self._serial = None
        self._last_open_attempt = 0.0
        self._last_message = ""
        self._connected = False

    def update(self, buttons, coin_sensor) -> None:
        serial_port = self._ensure_serial()
        if serial_port is None:
            return

        try:
            while serial_port.in_waiting:
                line = serial_port.readline().decode("utf-8", errors="ignore").strip()
                if line:
                    self._handle_line(line, buttons, coin_sensor)
        except OSError:
            self.close()

    def send(self, command: str) -> None:
        serial_port = self._ensure_serial()
        if serial_port is None:
            return
        try:
            serial_port.write((command.strip() + "\n").encode("utf-8"))
        except OSError:
            self.close()

    def status(self) -> str:
        if not self._connected:
            return "offline"
        return self._last_message or "connected"

    def close(self) -> None:
        if self._serial is not None:
            try:
                self._serial.close()
            except OSError:
                pass
        self._serial = None
        self._connected = False

    def _ensure_serial(self):
        if self._serial is not None:
            return self._serial

        now = time.time()
        if now - self._last_open_attempt < 2.0:
            return None
        self._last_open_attempt = now

        try:
            import serial

            self._serial = serial.Serial(self.port, self.baudrate, timeout=0)
            self._connected = True
            self._last_message = f"open {self.port}"
            return self._serial
        except (ImportError, OSError):
            self._serial = None
            self._connected = False
            return None

    def _handle_line(self, line: str, buttons, coin_sensor) -> None:
        self._last_message = line
        parts = line.split()
        if not parts:
            return

        if parts[0] == "BTN" and len(parts) >= 3:
            logical = parts[1]
            state = parts[2]
            buttons.set_external_state(logical, state == "down")
        elif parts[0] == "COIN":
            coin_sensor.trigger_external()
