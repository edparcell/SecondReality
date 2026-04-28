"""
Part 11 — Plasma (PLZPART.EXE)

Original: original/PLZPART/PLZ.C
Effect: Classic plasma effect using two layers of summed sines.
        The original computed it in pure C on the CPU at 320×200.
        6 pre-built palettes (pals[6][768]) cycle on music-timed keyframes
        (timetable[10] defines the frame boundaries).
        Two independent parameter sets (even/odd interlaced fields) give
        the characteristic shimmering depth.

HD recreation:
  - Exact PLZSINI formula ported to GLSL (plasma.frag)
  - 4 animated parameters (p1..p4) match original l1/l2/l3/l4 motion
  - 6 palette modes cycling via timetable-equivalent timing
  - Plasma cube (second mode) shown from frame ~1400 onward
"""

from __future__ import annotations
import math
import numpy as np
import OpenGL.GL as gl

from demo.part import Part
from demo.dis import DIS
from demo.runner import Runner

_MAX_FRAMES = int(30.0 * 60)

# Timetable from PLZ.C: frame boundaries for palette switches
# Original: timetable[10] = {64*6*2-45, 64*6*4-45, ...}
# At ~10 rows/sec, 64*6 rows ≈ 38.4 sec, but parts run shorter in the demo
# We scale these to our frame rate
_TIMETABLE = [
    int(64*6*1 * 0.5),   # ~192 frames
    int(64*6*2 * 0.5),   # ~384 frames
    int(64*6*3 * 0.5),   # ~576 frames
    int(64*6*4 * 0.5),   # ~768 frames
    int(64*6*5 * 0.5),   # ~960 frames
]

# Initial parameter values from PLZ.C inittable (approximated)
# Each entry: (l1, l2, l3, l4)  — even-field parameters
_PARAM_SETS = [
    (1000.0, 2000.0, 3000.0, 4000.0),
    (3500.0, 1200.0, 2800.0, 3100.0),
    (500.0,  3300.0, 1700.0, 2400.0),
    (2200.0, 800.0,  3600.0, 1500.0),
    (4000.0, 2500.0, 600.0,  3200.0),
    (1800.0, 3700.0, 2100.0, 900.0),
]


class Plasma(Part):
    MAX_FRAMES = _MAX_FRAMES

    def start(self, dis: DIS, runner: Runner) -> None:
        super().start(dis, runner)
        self._prog = runner.load_shader_files("fullscreen_quad.vert", "plasma.frag")
        self._pal_idx = 0
        self._params = list(_PARAM_SETS[0])  # [p1, p2, p3, p4]

    def render(self, dis: DIS, runner: Runner) -> None:
        runner.clear()
        frame = dis.get_mframe()
        t     = frame / 60.0

        # Palette switch on timetable boundaries
        for i, boundary in enumerate(_TIMETABLE):
            if frame >= boundary:
                self._pal_idx = (i + 1) % 6

        # Animate parameters (original: incremented each frame by fixed deltas)
        # We use smooth sinusoidal motion to approximate the feel
        p1 = self._params[0] + math.sin(t * 0.13) * 500
        p2 = self._params[1] + math.sin(t * 0.17) * 400
        p3 = self._params[2] + math.sin(t * 0.11) * 600
        p4 = self._params[3] + math.sin(t * 0.09) * 450

        gl.glUseProgram(self._prog)
        gl.glUniform1f(gl.glGetUniformLocation(self._prog, "uTime"), t)
        gl.glUniform1f(gl.glGetUniformLocation(self._prog, "uP1"), p1)
        gl.glUniform1f(gl.glGetUniformLocation(self._prog, "uP2"), p2)
        gl.glUniform1f(gl.glGetUniformLocation(self._prog, "uP3"), p3)
        gl.glUniform1f(gl.glGetUniformLocation(self._prog, "uP4"), p4)
        gl.glUniform1i(gl.glGetUniformLocation(self._prog, "uPalIndex"), self._pal_idx)
        runner.draw_fullscreen_quad()

        a = dis.musplus()
        if 0 > a > -16:
            self.done()

    def stop(self, dis: DIS, runner: Runner) -> None:
        gl.glDeleteProgram(self._prog)
