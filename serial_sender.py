import serial
import time
from sender_base import GcodeSenderBase

class SerialGcodeSender(GcodeSenderBase):
    def __init__(self, port_name: str, baudrate: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.port_name = port_name
        self.baudrate = baudrate

    def run(self):
        try:
            ser = serial.Serial(self.port_name, self.baudrate, timeout=1.0)
        except Exception as e:
            self._emit_error(f"Serial open error: {e}")
            if self.on_done: self.on_done()
            return

        self._emit_log(f"Connected via Serial {self.port_name} @ {self.baudrate}")
        
        # Wake up GRBL
        ser.write(b"\r\n\r\n")
        time.sleep(2)
        ser.reset_input_buffer()

        try:
            for idx, raw in enumerate(self.gcode_lines):
                if not self._running: break
                line = raw.strip()
                if not line or line.startswith(("//", ";", "(")): continue

                self._emit_line_start(idx)
                msg = (line + "\n").encode("ascii", errors="ignore")
                
                ser.write(msg)
                
                # Wait for 'ok'
                got_reply = False
                while not got_reply and self._running:
                    line_in = ser.readline().decode("ascii", errors="ignore").strip()
                    if not line_in:
                        continue
                    
                    # self._emit_log(f"< {line_in}") 
                    low = line_in.lower()
                    if low.startswith("ok"):
                        got_reply = True
                    elif "error" in low or "alarm" in low:
                        self._emit_error(f"GRBL Error: {line_in}")
                        if "alarm" in low: self._running = False
                        got_reply = True

            self._emit_log("Serial Job finished.")

        finally:
            ser.close()
            if self.on_done: self.on_done()

