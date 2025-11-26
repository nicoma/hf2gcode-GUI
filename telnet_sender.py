import socket
from sender_base import GcodeSenderBase

class TelnetGcodeSender(GcodeSenderBase):
    def __init__(self, host: str, port: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.host = host
        self.port = port

    def run(self):
        try:
            s = socket.create_connection((self.host, self.port), timeout=5.0)
            s.settimeout(None) # Blocking for stream
            # Initial dummy read often needed for some telnet servers
            try:
                s.settimeout(10.0)
                s.recv(4096)
                s.settimeout(None)
            except socket.timeout:
                pass
        except Exception as e:
            self._emit_error(f"Telnet connect error: {e}")
            if self.on_done: self.on_done()
            return

        self._emit_log(f"Connected via Telnet to {self.host}:{self.port}")
        buffer = b""

        try:
            # Wake up GRBL
            s.sendall(b"\r\n\r\n")
            import time
            time.sleep(1)

            for idx, raw in enumerate(self.gcode_lines):
                if not self._running: break
                line = raw.strip()
                if not line or line.startswith(("//", ";", "(")): continue

                self._emit_line_start(idx)
                msg = (line + "\n").encode("ascii", errors="ignore")
                
                try:
                    s.sendall(msg)
                except Exception as e:
                    self._emit_error(f"Send error: {e}")
                    break

                # Wait for "ok"
                got_reply = False
                while not got_reply and self._running:
                    try:
                        chunk = s.recv(1024)
                        if not chunk: break
                        buffer += chunk
                    except Exception as e:
                        self._emit_error(f"Recv error: {e}")
                        break

                    while b"\n" in buffer:
                        l, buffer = buffer.split(b"\n", 1)
                        reply = l.decode("ascii", errors="ignore").strip()
                        if not reply: continue
                        # self._emit_log(f"< {reply}") # Too verbose?
                        low = reply.lower()
                        if low.startswith("ok"):
                            got_reply = True
                        elif "error" in low or "alarm" in low:
                            self._emit_error(f"GRBL Error: {reply}")
                            if "alarm" in low: self._running = False # Stop on alarm
                            got_reply = True # Treat as handled to move on or stop

            self._emit_log("Telnet Job finished.")

        finally:
            s.close()
            if self.on_done: self.on_done()

