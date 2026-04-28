"""
Part 09 — Mountain / Forest Scroll (MNTSCRL.EXE)

Original: original/FOREST/ or MNTSCRL/
Effect: A mountain/forest panorama scrolls horizontally (parallax).
        Multiple depth layers scroll at different speeds (classic parallax).
        The original loaded a wide .LBM bitmap and scrolled it.

HD recreation:
  - Procedural mountain silhouettes: 3 layers at different depths
  - Stars in the sky (parallax with mountains)
  - Each layer scrolls at a different speed (near/mid/far)
  - Palette: night sky blue-black gradient
  - Moonlight: bright circle with glow
"""

from __future__ import annotations
import math
import numpy as np
import OpenGL.GL as gl

from demo.part import Part
from demo.dis import DIS
from demo.runner import Runner

_MAX_FRAMES = int(20.0 * 60)


class ForestScroll(Part):
    MAX_FRAMES = _MAX_FRAMES

    def start(self, dis: DIS, runner: Runner) -> None:
        super().start(dis, runner)
        self._prog = runner.load_shader_files("fullscreen_quad.vert",
                                               "forest.frag")

    def render(self, dis: DIS, runner: Runner) -> None:
        runner.clear(0.0, 0.01, 0.05)

        frame = dis.get_mframe()
        t     = frame / 60.0

        gl.glUseProgram(self._prog)
        gl.glUniform1f(gl.glGetUniformLocation(self._prog, "uTime"), t)
        gl.glUniform1f(gl.glGetUniformLocation(self._prog, "uScroll"), t * 0.08)
        gl.glUniform1f(gl.glGetUniformLocation(self._prog, "uAspect"),
                       float(runner.width) / runner.height)
        runner.draw_fullscreen_quad()

        a = dis.musplus()
        if 0 > a > -16:
            self.done()

    def stop(self, dis: DIS, runner: Runner) -> None:
        gl.glDeleteProgram(self._prog)
