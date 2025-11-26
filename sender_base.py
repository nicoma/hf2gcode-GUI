import threading
from typing import Callable, List, Optional

LogCallback = Callable[[str], None]
LineCallback = Callable[[int], None]
ErrorCallback = Callable[[str], None]

class GcodeSenderBase(threading.Thread):
    def __init__(
        self,
        gcode_lines: List[str],
        on_log: Optional[LogCallback] = None,
        on_line_start: Optional[LineCallback] = None,
        on_error: Optional[ErrorCallback] = None,
        on_done: Optional[Callable[[], None]] = None,
    ):
        super().__init__(daemon=True)
        self.gcode_lines = gcode_lines
        self.on_log = on_log
        self.on_line_start = on_line_start
        self.on_error = on_error
        self.on_done = on_done
        self._running = True

    def stop(self):
        self._running = False

    def _emit_log(self, msg: str):
        if self.on_log: self.on_log(msg)

    def _emit_error(self, msg: str):
        if self.on_error: self.on_error(msg)

    def _emit_line_start(self, idx: int):
        if self.on_line_start: self.on_line_start(idx)

