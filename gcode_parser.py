# gcode_parser.py
from dataclasses import dataclass
from typing import List
import re

XY_RE_X = re.compile(r"X(-?\d+(\.\d+)?)")
XY_RE_Y = re.compile(r"Y(-?\d+(\.\d+)?)")


@dataclass
class Segment:
    line_index: int
    x1: float
    y1: float
    x2: float
    y2: float
    is_draw: bool = True


def parse_segments(gcode_text: str) -> List[Segment]:
    segments: List[Segment] = []
    lines = gcode_text.splitlines()

    x = y = 0.0
    last_x = last_y = 0.0

    for idx, raw in enumerate(lines):
        line = raw.strip()
        if not line or line.startswith(("//", ";", "(")):
            continue

        upper = line.upper()
        is_g0 = upper.startswith("G0") or " G0" in upper
        is_g1 = upper.startswith("G1") or " G1" in upper

        mx = XY_RE_X.search(upper)
        my = XY_RE_Y.search(upper)
        if mx:
            x = float(mx.group(1))
        if my:
            y = float(my.group(1))

        if is_g0:
            last_x, last_y = x, y
        elif is_g1:
            segments.append(Segment(idx, last_x, last_y, x, y, True))
            last_x, last_y = x, y

    return segments

