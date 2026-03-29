"""
Part 13 — Mirror Ball Scroll (RAYSCRL.EXE / WATER)

Original: original/WATER/ or RAYSCRL/
Effect: A reflective mirror-ball (disco ball) floats above a scrolling
        ground plane. The original used per-pixel raycast reflection
        mapping and a horizontal scroller.

HD recreation:
  - GLSL sphere raycast: compute ray-sphere intersection, reflect,
    sample environment map
  - Environment: procedural starfield + gradient
  - Scrolling text banner below the ball
  - Specular highlights make it look chrome/glass
"""

from __future__ import annotations
import math
import numpy as np
import OpenGL.GL as gl

from demo.part import Part
from demo.dis import DIS
from demo.runner import Runner

_MAX_FRAMES = int(20.0 * 60)


class MirrorBallScroll(Part):
    MAX_FRAMES = _MAX_FRAMES

    def start(self, dis: DIS, runner: Runner) -> None:
        super().start(dis, runner)
        self._prog = runner.load_shader_files("fullscreen_quad.vert",
                                               "mirror_ball.frag")

    def render(self, dis: DIS, runner: Runner) -> None:
        runner.clear()
        frame = dis.get_mframe()
        t     = frame / 60.0

        gl.glUseProgram(self._prog)
        gl.glUniform1f(gl.glGetUniformLocation(self._prog, "uTime"), t)
        gl.glUniform1f(gl.glGetUniformLocation(self._prog, "uAspect"),
                       float(runner.width) / runner.height)
        gl.glUniform1f(gl.glGetUniformLocation(self._prog, "uScroll"), t * 0.15)
        runner.draw_fullscreen_quad()

        a = dis.musplus()
        if 0 > a > -16:
            self.done()

    def stop(self, dis: DIS, runner: Runner) -> None:
        gl.glDeleteProgram(self._prog)
