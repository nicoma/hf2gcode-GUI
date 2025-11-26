# gcode_generator.py
import subprocess
from dataclasses import dataclass
from typing import Optional, List


HF2GCODE_CMD = "../hf2gcode"  # To adjust for windows



@dataclass
class Hf2GcodeParams:
    font: str = "rowmans"
    scale: float = 0.2
    feed: int = 200
    xoffset: float = 0.0
    yoffset: float = 0.0
    z_down: float = -3.0
    z_up: float = 3.0
    align: str = "left"
    interline: float = 8.0
    precision: int = 3
    inch: bool = False
    min_gcode: bool = True
    no_pre: bool = False
    no_post: bool = False

    # Limites physiques robot
    robot_x_min: float = 0.0
    robot_x_max: float = 100.0
    robot_y_min: float = -50.0
    robot_y_max: float = 100.0

    # Zone sûre (avec marges, robot_y_max_effective, etc.)
    safe_x_min: float = 0.0
    safe_x_max: float = 0.0
    safe_y_min: float = 0.0
    safe_y_max: float = 0.0

    margin: float = 0.0

def build_cmd(params: Hf2GcodeParams) -> List[str]:
    cmd = [HF2GCODE_CMD]

    if params.font:
        cmd += ["--font", params.font]
    cmd += ["--scale", str(params.scale)]
    cmd += ["--feed", str(params.feed)]
    cmd += ["--xoffset", str(params.xoffset)]
    cmd += ["--yoffset", str(params.yoffset)]
    cmd += ["--z-down", str(params.z_down)]
    cmd += ["--z-up", str(params.z_up)]

    if params.align == "left":
        cmd += ["--align-left"]
    elif params.align == "center":
        cmd += ["--align-center"]
    elif params.align == "right":
        cmd += ["--align-right"]

    cmd += ["--interline", str(params.interline)]
    cmd += ["--precision", str(params.precision)]

    if params.min_gcode:
        cmd += ["--min-gcode"]
    if params.no_pre:
        cmd += ["--no-pre"]
    if params.no_post:
        cmd += ["--no-post"]
    if params.inch:
        cmd += ["--inch"]

    return cmd


def _extract_val(line: str, key: str) -> float | None:
    """
    Extrait la valeur numérique associée à une lettre (key) dans une ligne G-code.
    Exemple : _extract_val("G1 X12.5 Y10", "X") -> 12.5
    """
    if not line:
        return None
    
    # Nettoyage des commentaires
    clean_line = line.split('(', 1)[0].split(';', 1)[0].strip()
    if not clean_line:
        return None

    # Recherche basique : on découpe par espaces
    # Attention : cela suppose un G-code bien formaté type "X12.3" (collé)
    parts = clean_line.upper().split()
    key = key.upper()

    for p in parts:
        if p.startswith(key) and len(p) > len(key):
            try:
                return float(p[len(key):])
            except ValueError:
                continue
    return None


def filter_by_bounds(gcode: str, params: Hf2GcodeParams) -> str:
    """
    delete points out of the robot area :
    [robot_x_min + margin ; robot_x_max - margin] x
    [robot_y_min + margin ; robot_y_max - margin].
    """
    x_min = params.robot_x_min + params.margin
    x_max = params.robot_x_max - params.margin
    y_min = params.robot_y_min + params.margin
    y_max = params.robot_y_max - params.margin

    lines = gcode.splitlines()
    keep: list[str] = []

    for line in lines:
        s = line.strip()
        # Remove empty line
        if not s or s.startswith("("):
            keep.append(line)
            continue

        x = _extract_val(line, "X")
        y = _extract_val(line, "Y")

        # Out of X
        if x is not None and (x < x_min or x > x_max):
            continue

        # Out of Y
        if y is not None and (y < y_min or y > y_max):
            continue

        keep.append(line)

    return "\n".join(keep)



def _extract_z(line: str) -> float | None:
    return _extract_val(line, "Z")


def _has_xy(line: str) -> bool:
    if not line or line.strip().startswith("("):
        return False
    upper = line.upper()
    return "X" in upper or "Y" in upper


def _is_comment_or_empty(line: str) -> bool:
    s = line.strip()
    if not s:
        return True
    if s.startswith("(") and s.endswith(")"):
        return True
    return False


def optimize_pen_lift(gcode: str) -> str:
    """
    Optimization :
    1. Remove duplicate
    2. Remove useless Z move 
    """
    lines = gcode.splitlines()
    

    deduplicated_lines = []
    last_active_command = None

    for line in lines:
        stripped = line.strip()
        

        if _is_comment_or_empty(line):
            deduplicated_lines.append(line)
            continue
            
      
        if stripped == last_active_command:
       
            continue
        else:
         
            deduplicated_lines.append(line)
            last_active_command = stripped

  
    lines = deduplicated_lines
    keep: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]

        if _is_comment_or_empty(line):
            i += 1
            continue

        j = i + 1
        while j < len(lines) and _is_comment_or_empty(lines[j]):
            j += 1

        if j >= len(lines):
            keep.append(line)
            i += 1
            continue

        current = line.strip()
        next_line = lines[j].strip()

        z1 = _extract_z(current)
        z2 = _extract_z(next_line)
        has_xy1 = _has_xy(current)
        has_xy2 = _has_xy(next_line)

        # Detection useless back and forth Z move
        if (
            z1 is not None
            and z2 is not None
            and not has_xy1
            and not has_xy2
            and abs(z2 + z1) < 1e-6
        ):
            # Jump instruction
            i = j + 1
            continue

        keep.append(line)
        i += 1

    return "\n".join(keep)



def generate_gcode(text: str, params: Hf2GcodeParams) -> str:
    
    cmd = build_cmd(params)
    proc = subprocess.run(
        cmd,
        input=text,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or "hf2gcode returned non-zero")
    
    raw_gcode = proc.stdout

    # 2. Filtering
    filtered_gcode = filter_by_bounds(raw_gcode, params)

    return filtered_gcode
