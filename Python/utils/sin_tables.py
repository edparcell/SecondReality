"""
Integer sine lookup tables — mirrors the original SIN1024.INC / SIN4096.INC.

Original tables:
  SIN1024: 1024 entries, range [-1024, 1024]   (s16, period = 1024)
  SIN4096: 4096 entries, range [-4096, 4096]   (s16, period = 4096)

Usage in the original:
  value = sin1024[angle & 1023]   # angle in units of 1/1024 turn
  value = sin4096[angle & 4095]   # angle in units of 1/4096 turn

These are used for all trigonometric calculations in the demo — no
floating-point math was used on 486-era hardware for real-time effects.
"""

import math
import numpy as np

# --- SIN1024 ---------------------------------------------------------------
# Period 1024, amplitude 1024 (integer range -1024..1024)
_N1 = 1024
SIN1024 = np.array(
    [int(round(math.sin(2 * math.pi * i / _N1) * _N1)) for i in range(_N1)],
    dtype=np.int32
)
COS1024 = np.array(
    [int(round(math.cos(2 * math.pi * i / _N1) * _N1)) for i in range(_N1)],
    dtype=np.int32
)

# --- SIN4096 ---------------------------------------------------------------
# Period 4096, amplitude 4096 (integer range -4096..4096)
_N4 = 4096
SIN4096 = np.array(
    [int(round(math.sin(2 * math.pi * i / _N4) * _N4)) for i in range(_N4)],
    dtype=np.int32
)
COS4096 = np.array(
    [int(round(math.cos(2 * math.pi * i / _N4) * _N4)) for i in range(_N4)],
    dtype=np.int32
)


def isin(angle: int, table: np.ndarray = SIN1024) -> int:
    """Integer sine lookup.  angle wraps modulo len(table)."""
    return int(table[angle % len(table)])


def icos(angle: int, table: np.ndarray = COS1024) -> int:
    """Integer cosine lookup.  angle wraps modulo len(table)."""
    return int(table[angle % len(table)])


def isin4(angle: int) -> int:
    """Integer sine using the 4096-entry table."""
    return int(SIN4096[angle & 4095])


def icos4(angle: int) -> int:
    """Integer cosine using the 4096-entry table."""
    return int(COS4096[angle & 4095])
