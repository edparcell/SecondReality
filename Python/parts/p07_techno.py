"""
Part 07 — Techno Bars (TECHNO.EXE)

Original: original/TECHNO/KOE.C (actually JPLOGO/JP.C logic)
Effect: EGA-style interference bars — horizontal stripes that cycle through
        4 EGA bitplanes, creating a strobing colour pattern.
        On every 8th music row (the beat), the entire screen flashes white.
        CRTC start address is incremented each frame for a scrolling effect.

HD recreation:
  - Interference bars via GLSL: animated horizontal banding with colour cycling
  - Beat flash: white overlay on musrow() & 7 == 7
  - Vertical scroll of the pattern (CRTC start address equivalent)
  - EGA palette approximation: 4 cycling colour sets
"""

from __future__ import annotations
import math
import numpy as np
import OpenGL.GL as gl

from demo.part import Part
from demo.dis import DIS
from demo.runner import Runner

_MAX_FRAMES = int(22.0 * 60)


class TechnoBars(Part):
    MAX_FRAMES = _MAX_FRAMES

    def start(self, dis: DIS, runner: Runner) -> None:
        super().start(dis, runner)
        self._prog = runner.load_shader_files("fullscreen_quad.vert",
                                               "techno.frag")
        self._flash = 0.0

    def render(self, dis: DIS, runner: Runner) -> None:
        runner.clear()
        frame = dis.get_mframe()
        t     = frame / 60.0

        # Beat flash on every 8th row
        row = dis.musrow()
        if row & 7 == 7:
            self._flash = 1.0
        self._flash *= 0.7  # decay

        gl.glUseProgram(self._prog)
        gl.glUniform1f(gl.glGetUniformLocation(self._prog, "uTime"), t)
        gl.glUniform1f(gl.glGetUniformLocation(self._prog, "uScroll"), frame * 0.4)
        gl.glUniform1f(gl.glGetUniformLocation(self._prog, "uFlash"), self._flash)
        runner.draw_fullscreen_quad()

        a = dis.musplus()
        if 0 > a > -16:
            self.done()

    def stop(self, dis: DIS, runner: Runner) -> None:
        gl.glDeleteProgram(self._prog)
