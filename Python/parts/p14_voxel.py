"""
Part 14 — Voxel Landscape / 3D Sine Field (3DSINFLD.EXE / HARD)

Original: original/HARD/MAIN.C + original/COMAN/
Effect: Comanche-style voxel heightmap — the camera flies over a
        procedural landscape. The original used a column-based raycast
        rendering engine. This was the most technically impressive part
        of the demo at the time, showing a pre-Comanche-style terrain renderer.

HD recreation:
  - Full GLSL fragment shader raycast (voxel.frag)
  - Procedurally generated heightmap (layered sines — redrawn)
  - Animated camera flyover path
  - Sky gradient + distance fog
"""

from __future__ import annotations
import math
import numpy as np
import OpenGL.GL as gl

from demo.part import Part
from demo.dis import DIS
from demo.runner import Runner

_MAX_FRAMES = int(25.0 * 60)


class VoxelLandscape(Part):
    MAX_FRAMES = _MAX_FRAMES

    def start(self, dis: DIS, runner: Runner) -> None:
        super().start(dis, runner)
        self._prog = runner.load_shader_files("fullscreen_quad.vert", "voxel.frag")

    def render(self, dis: DIS, runner: Runner) -> None:
        runner.clear(0.4, 0.55, 0.75)
        frame = dis.get_mframe()
        t     = frame / 60.0

        # Camera flyover path: slow sweep with banking turns
        cam_x = math.sin(t * 0.15) * 120.0 + t * 30.0
        cam_z = t * 60.0
        cam_y = 140.0 + math.sin(t * 0.25) * 20.0

        # Yaw: follows a sinusoidal path
        yaw   = math.sin(t * 0.2) * 0.4
        pitch = -0.05 + math.sin(t * 0.3) * 0.03

        gl.glUseProgram(self._prog)
        gl.glUniform3f(gl.glGetUniformLocation(self._prog, "uCamPos"),
                       cam_x, cam_y, cam_z)
        gl.glUniform1f(gl.glGetUniformLocation(self._prog, "uCamAngle"), yaw)
        gl.glUniform1f(gl.glGetUniformLocation(self._prog, "uCamPitch"), pitch)
        gl.glUniform1f(gl.glGetUniformLocation(self._prog, "uTime"), t)
        gl.glUniform2f(gl.glGetUniformLocation(self._prog, "uResolution"),
                       float(runner.width), float(runner.height))
        runner.draw_fullscreen_quad()

        a = dis.musplus()
        if 0 > a > -16:
            self.done()

    def stop(self, dis: DIS, runner: Runner) -> None:
        gl.glDeleteProgram(self._prog)
