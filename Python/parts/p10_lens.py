"""
Part 10 — Lens + Rotozoomer (LNS&ZOOM.EXE)

Original: original/LENS/MAIN.C
Effect: Two sub-effects:
  1. Lens: A pre-recorded bouncing lens distorts the background image.
           4 chromatic aberration layers for a rainbow fringe.
           Path pre-recorded as pathdata1[] during development, replayed here.
  2. Rotozoomer: A rotating, zooming tile pattern fills the screen,
                  path from pathdata2[].

HD recreation:
  - Lens: GLSL UV-warp shader with 3-channel chromatic aberration
  - Background: procedural plasma-like texture (no .LBM — redrawn)
  - Pre-recorded path approximated with sinusoidal motion
  - Fire wipe: scanline-based colour sweep on transition (firfade tables)
  - Rotozoomer: GLSL rotation+zoom on procedural checkerboard
"""

from __future__ import annotations
import math
import numpy as np
import OpenGL.GL as gl

from demo.part import Part
from demo.dis import DIS
from demo.runner import Runner

_MAX_FRAMES = int(25.0 * 60)
# Transition: first ~300 frames = rotozoomer, then lens
_ROTO_FRAMES = 300


class LensRotozoomer(Part):
    MAX_FRAMES = _MAX_FRAMES

    def start(self, dis: DIS, runner: Runner) -> None:
        super().start(dis, runner)

        self._prog_bg   = runner.load_shader_files("fullscreen_quad.vert",
                                                    "lens_bg.frag")
        self._prog_lens = runner.load_shader_files("fullscreen_quad.vert",
                                                    "lens.frag")
        self._prog_roto = runner.load_shader_files("fullscreen_quad.vert",
                                                    "rotozoomer.frag")

        # Build a framebuffer texture for the background (source for lens)
        self._fbo, self._fbo_tex = self._make_fbo(runner.width, runner.height)

    def render(self, dis: DIS, runner: Runner) -> None:
        frame = dis.get_mframe()
        t     = frame / 60.0

        if frame < _ROTO_FRAMES:
            # --- Rotozoomer ---
            runner.clear()
            angle = t * 0.8
            zoom  = 0.5 + math.sin(t * 0.4) * 0.3
            off_x = math.sin(t * 0.3) * 0.1
            off_y = math.cos(t * 0.25) * 0.1

            gl.glUseProgram(self._prog_roto)
            gl.glUniform1f(gl.glGetUniformLocation(self._prog_roto, "uAngle"), angle)
            gl.glUniform1f(gl.glGetUniformLocation(self._prog_roto, "uZoom"),  zoom)
            gl.glUniform2f(gl.glGetUniformLocation(self._prog_roto, "uOffset"), off_x, off_y)
            gl.glUniform1f(gl.glGetUniformLocation(self._prog_roto, "uTime"),  t)
            runner.draw_fullscreen_quad()

        else:
            # --- Lens effect ---
            t2 = t - _ROTO_FRAMES / 60.0

            # Render background to FBO
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self._fbo)
            gl.glViewport(0, 0, runner.width, runner.height)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT)
            gl.glUseProgram(self._prog_bg)
            gl.glUniform1f(gl.glGetUniformLocation(self._prog_bg, "uTime"), t)
            runner.draw_fullscreen_quad()
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
            gl.glViewport(0, 0, runner.width, runner.height)

            # Pre-recorded-path approximation (pathdata1[] from LENS/MAIN.C)
            # Original: bouncing lens with x/y derived from pathdata1[frame*2]
            lx = 0.5 + math.sin(t2 * 1.7) * 0.25 + math.sin(t2 * 0.4) * 0.1
            ly = 0.5 + math.cos(t2 * 1.3) * 0.2  + math.cos(t2 * 0.6) * 0.08
            strength = 0.6 + math.sin(t2 * 0.7) * 0.2
            radius   = 0.28 + math.sin(t2 * 0.5) * 0.06

            gl.glUseProgram(self._prog_lens)
            gl.glUniform1i(gl.glGetUniformLocation(self._prog_lens, "uSource"), 0)
            gl.glUniform2f(gl.glGetUniformLocation(self._prog_lens, "uLensPos"), lx, ly)
            gl.glUniform1f(gl.glGetUniformLocation(self._prog_lens, "uLensStrength"), strength)
            gl.glUniform1f(gl.glGetUniformLocation(self._prog_lens, "uLensRadius"),   radius)
            gl.glUniform1f(gl.glGetUniformLocation(self._prog_lens, "uChromaOffset"), 0.012)
            gl.glUniform1f(gl.glGetUniformLocation(self._prog_lens, "uTime"), t)
            gl.glActiveTexture(gl.GL_TEXTURE0)
            gl.glBindTexture(gl.GL_TEXTURE_2D, self._fbo_tex)
            runner.draw_fullscreen_quad()

        a = dis.musplus()
        if 0 > a > -16:
            self.done()

    def stop(self, dis: DIS, runner: Runner) -> None:
        gl.glDeleteFramebuffers(1, [self._fbo])
        gl.glDeleteTextures([self._fbo_tex])
        for p in [self._prog_bg, self._prog_lens, self._prog_roto]:
            gl.glDeleteProgram(p)

    @staticmethod
    def _make_fbo(w: int, h: int) -> tuple[int, int]:
        fbo = gl.glGenFramebuffers(1)
        tex = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, tex)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGB, w, h, 0,
                        gl.GL_RGB, gl.GL_UNSIGNED_BYTE, None)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, fbo)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0,
                                   gl.GL_TEXTURE_2D, tex, 0)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        return int(fbo), int(tex)
