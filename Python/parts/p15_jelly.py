"""
Part 15 — Jelly Picture + Interference (JPLOGO.EXE)

Original: original/JPLOGO/JP.C (same file as TECHNO/KOE.C)
Effect: Three sub-phases:
  1. EGA interference boxes: `doit1/2/3` routines cycle through EGA bitplanes
     with the CRTC start address rotating to create interference boxes.
  2. Picture reveal: A bitmap (JP.LBM) slides in from the left with
     acceleration (`xpos += xposa++`), overshoots, then settles.
  3. Ripple wipe: `xpos = 320 + sin1024[ripple]/ripplep; ripplep *= 5/4`
     The image ripples horizontally with a decaying oscillation.

HD recreation:
  - Phase 1: interference GLSL (similar to techno.frag but different pattern)
  - Phase 2: procedural "picture" (abstract coloured image) slides in
  - Phase 3: horizontal ripple with exponentially decaying amplitude
"""

from __future__ import annotations
import math
import numpy as np
import OpenGL.GL as gl

from demo.part import Part
from demo.dis import DIS
from demo.runner import Runner

_MAX_FRAMES = int(20.0 * 60)
_PHASE1_END = 180   # frames of interference
_PHASE2_END = 420   # reveal complete
_PHASE3_END = _MAX_FRAMES


class JellyPicture(Part):
    MAX_FRAMES = _MAX_FRAMES

    def start(self, dis: DIS, runner: Runner) -> None:
        super().start(dis, runner)
        self._prog_inter  = runner.load_shader_files("fullscreen_quad.vert",
                                                      "jelly_inter.frag")
        self._prog_reveal = runner.load_shader_files("fullscreen_quad.vert",
                                                      "jelly_reveal.frag")

        # Reveal physics state (mirrors JP.C xpos/xposa)
        self._xpos  = float(runner.width)   # start off-screen right
        self._xposa = 0.0

    def render(self, dis: DIS, runner: Runner) -> None:
        frame = dis.get_mframe()
        t     = frame / 60.0

        if frame < _PHASE1_END:
            # Phase 1: EGA-style interference
            runner.clear()
            gl.glUseProgram(self._prog_inter)
            gl.glUniform1f(gl.glGetUniformLocation(self._prog_inter, "uTime"), t)
            gl.glUniform1f(gl.glGetUniformLocation(self._prog_inter, "uPhase"),
                           frame / _PHASE1_END)
            runner.draw_fullscreen_quad()

        elif frame < _PHASE2_END:
            # Phase 2: picture slides in from right
            # xpos = xpos + xposa; xposa++ until xpos <= 0
            if self._xpos > 0:
                self._xposa -= 2.5  # acceleration
                self._xpos  += self._xposa
                if self._xpos < 0:
                    self._xpos  = 0
                    self._xposa = 0

            runner.clear()
            gl.glUseProgram(self._prog_reveal)
            gl.glUniform1f(gl.glGetUniformLocation(self._prog_reveal, "uTime"), t)
            gl.glUniform1f(gl.glGetUniformLocation(self._prog_reveal, "uXOffset"),
                           self._xpos / runner.width)
            gl.glUniform1f(gl.glGetUniformLocation(self._prog_reveal, "uRipple"), 0.0)
            runner.draw_fullscreen_quad()

        else:
            # Phase 3: ripple wipe (decaying horizontal oscillation)
            # Original: ripplep *= 5/4 each frame (amplitude grows → dies)
            ripple_frame = frame - _PHASE2_END
            # Amplitude starts large and decays (ripplep grows → 1/ripplep shrinks)
            ripplep  = 1.0 + ripple_frame * 0.15
            ripple_amp = 1.0 / ripplep

            runner.clear()
            gl.glUseProgram(self._prog_reveal)
            gl.glUniform1f(gl.glGetUniformLocation(self._prog_reveal, "uTime"), t)
            gl.glUniform1f(gl.glGetUniformLocation(self._prog_reveal, "uXOffset"), 0.0)
            gl.glUniform1f(gl.glGetUniformLocation(self._prog_reveal, "uRipple"),
                           ripple_amp * math.sin(ripple_frame * 0.3))
            runner.draw_fullscreen_quad()

        a = dis.musplus()
        if 0 > a > -16:
            self.done()

    def stop(self, dis: DIS, runner: Runner) -> None:
        gl.glDeleteProgram(self._prog_inter)
        gl.glDeleteProgram(self._prog_reveal)
