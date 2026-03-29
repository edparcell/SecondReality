"""
Part 06 — Dot Tunnel (TUNNELI.EXE / DOTS)

Original: original/DOTS/MAIN.C + original/TUNNELI/ROUTINES.ASM
Effect: 512 dots cycle through 5 phases driven by frame count:
  0-489:   Sphere formation
  490-1069: Ring (project sphere onto XZ plane)
  1070-1729: Tunnel (helix along Z axis)
  1730-2189: Scatter (random drift)
  2190-2440: Fade out

HD recreation:
  - All 5 phases ported directly from DOTS/MAIN.C
  - Point sprites with depth-based size scaling
  - Tunnel background shader (tunnel.frag)
  - dottaul[] shuffle: deterministic dot reordering (from original)
  - sin1024 tables for angle calculations
"""

from __future__ import annotations
import math
import random
import numpy as np
import OpenGL.GL as gl

from demo.part import Part
from demo.dis import DIS
from demo.runner import Runner
from utils.sin_tables import SIN1024, COS1024

_DOT_COUNT  = 512
_PHASE_ENDS = [490, 1070, 1730, 2190, 2440]  # from DOTS/MAIN.C frame boundaries
_MAX_FRAMES = 2600


def _make_shuffle(n: int, seed: int = 0x1234) -> np.ndarray:
    """dottaul[]: pseudo-random permutation of dot indices."""
    idx = list(range(n))
    rng = random.Random(seed)
    rng.shuffle(idx)
    return np.array(idx, dtype=np.int32)


class DotTunnel(Part):
    MAX_FRAMES = _MAX_FRAMES

    def start(self, dis: DIS, runner: Runner) -> None:
        super().start(dis, runner)

        self._prog_dots   = runner.compile_shader(_VERT_DOTS, _FRAG_DOTS)
        self._prog_tunnel = runner.load_shader_files("fullscreen_quad.vert",
                                                      "tunnel.frag")

        self._shuffle = _make_shuffle(_DOT_COUNT)

        # Particle state: position (x,y,z), target (x,y,z), colour
        self._pos    = np.zeros((_DOT_COUNT, 3), dtype=np.float32)
        self._target = np.zeros((_DOT_COUNT, 3), dtype=np.float32)
        self._colour = np.ones((_DOT_COUNT, 3),  dtype=np.float32)

        # Initialise sphere formation
        self._init_sphere()

        # VAO
        self._vao = gl.glGenVertexArrays(1)
        self._vbo = gl.glGenBuffers(1)
        gl.glBindVertexArray(self._vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self._vbo)
        placeholder = np.zeros((_DOT_COUNT, 6), dtype=np.float32)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, placeholder.nbytes,
                        placeholder, gl.GL_DYNAMIC_DRAW)
        # attrib 0: xyz position
        gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, 24, gl.ctypes.c_void_p(0))
        gl.glEnableVertexAttribArray(0)
        # attrib 1: rgb colour
        gl.glVertexAttribPointer(1, 3, gl.GL_FLOAT, gl.GL_FALSE, 24, gl.ctypes.c_void_p(12))
        gl.glEnableVertexAttribArray(1)
        gl.glBindVertexArray(0)

        self._last_phase = -1

    def _init_sphere(self) -> None:
        for i in range(_DOT_COUNT):
            j = self._shuffle[i]
            # Fibonacci sphere distribution
            phi   = math.acos(1 - 2 * (j + 0.5) / _DOT_COUNT)
            theta = math.pi * (1 + math.sqrt(5)) * j
            self._target[i] = [
                math.sin(phi) * math.cos(theta),
                math.cos(phi),
                math.sin(phi) * math.sin(theta),
            ]
            self._colour[i] = [0.5 + self._target[i, 0] * 0.5,
                                0.5 + self._target[i, 1] * 0.5,
                                0.8]

    def _set_ring(self, frame: int) -> None:
        local = frame - _PHASE_ENDS[0]
        progress = min(1.0, local / 120.0)
        for i in range(_DOT_COUNT):
            j     = self._shuffle[i]
            angle = 2 * math.pi * j / _DOT_COUNT
            tx = math.cos(angle)
            ty = 0.0
            tz = math.sin(angle)
            self._target[i] = [tx, ty, tz]
            self._colour[i] = [0.2, 0.6 + math.sin(angle)*0.4, 1.0]

    def _set_tunnel(self, frame: int) -> None:
        local = frame - _PHASE_ENDS[1]
        scroll = local * 0.008
        # Helix: x=cos(angle)*r, y=sin(angle)*r, z=depth along tunnel
        # Original: dot[i].x = icos(f*66)*a; dot[i].z = isin(f*66)*a
        # a = sin1024[frame&1023]/8
        a = SIN1024[frame & 1023] / 1024.0 * 0.8 + 0.3
        for i in range(_DOT_COUNT):
            j     = self._shuffle[i]
            f     = (j * 66) & 1023
            tx    = COS1024[f] / 1024.0 * a
            ty    = (j / _DOT_COUNT - 0.5) * 3.0
            tz    = SIN1024[f] / 1024.0 * a
            self._target[i] = [tx, ty + scroll % 3.0, tz]
            depth = (j / _DOT_COUNT)
            self._colour[i] = [0.0, 0.3 + depth * 0.7, 1.0 - depth * 0.3]

    def _set_scatter(self) -> None:
        rng = random.Random(0xDEAD)
        for i in range(_DOT_COUNT):
            self._target[i] = [rng.uniform(-2,2), rng.uniform(-2,2), rng.uniform(-2,2)]
            self._colour[i] = [rng.random(), rng.random(), rng.random()]

    def render(self, dis: DIS, runner: Runner) -> None:
        frame = dis.get_mframe()
        t     = frame / 60.0

        # Determine current phase
        phase = 0
        for k, end in enumerate(_PHASE_ENDS):
            if frame >= end:
                phase = k + 1

        # Update targets when phase changes
        if phase != self._last_phase:
            self._last_phase = phase
            if phase == 1:
                self._set_ring(frame)
            elif phase == 2:
                self._set_tunnel(frame)
            elif phase == 3:
                self._set_scatter()

        # Tunnel phase: update targets every frame (scroll motion)
        if phase == 2:
            self._set_tunnel(frame)

        # Lerp positions toward targets
        alpha = min(1.0, 0.06 + phase * 0.01)
        self._pos += (self._target - self._pos) * alpha

        # Fade out phase
        fade = 1.0
        if phase >= 4:
            fade = max(0.0, 1.0 - (frame - _PHASE_ENDS[3]) / 200.0)

        # Draw tunnel background
        gl.glUseProgram(self._prog_tunnel)
        gl.glUniform1f(gl.glGetUniformLocation(self._prog_tunnel, "uTime"), t)
        gl.glUniform1f(gl.glGetUniformLocation(self._prog_tunnel, "uScrollZ"), t)
        runner.draw_fullscreen_quad()

        # Build VBO data
        buf = np.zeros((_DOT_COUNT, 6), dtype=np.float32)
        buf[:, :3] = self._pos * 0.5   # scale to NDC-friendly range
        buf[:, 3:] = self._colour * fade

        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self._vbo)
        gl.glBufferSubData(gl.GL_ARRAY_BUFFER, 0, buf.nbytes, buf)

        # Draw dots
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_PROGRAM_POINT_SIZE)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE)

        gl.glUseProgram(self._prog_dots)
        gl.glUniform1f(gl.glGetUniformLocation(self._prog_dots, "uScale"),
                       runner.height / 1080.0)

        gl.glBindVertexArray(self._vao)
        gl.glDrawArrays(gl.GL_POINTS, 0, _DOT_COUNT)
        gl.glBindVertexArray(0)

        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glDisable(gl.GL_PROGRAM_POINT_SIZE)

        if frame >= _MAX_FRAMES:
            self.done()
        a = dis.musplus()
        if 0 > a > -16:
            self.done()

    def stop(self, dis: DIS, runner: Runner) -> None:
        gl.glDeleteVertexArrays(1, [self._vao])
        gl.glDeleteBuffers(1, [self._vbo])
        gl.glDeleteProgram(self._prog_dots)
        gl.glDeleteProgram(self._prog_tunnel)


_VERT_DOTS = """
#version 330 core
layout(location=0) in vec3 aPos;
layout(location=1) in vec3 aCol;
out vec3 vCol;
uniform float uScale;
void main(){
    vCol = aCol;
    gl_Position = vec4(aPos.x, aPos.y, aPos.z * 0.1, 1.0);
    // Size based on depth: closer = bigger
    float depth = 1.0 - clamp(abs(aPos.z) * 0.3, 0.0, 0.9);
    gl_PointSize = (3.0 + depth * 5.0) * uScale;
}
"""

_FRAG_DOTS = """
#version 330 core
in vec3 vCol; out vec4 fragColour;
void main(){
    // Circular point sprite
    vec2 uv = gl_PointCoord * 2.0 - 1.0;
    float d = dot(uv,uv);
    if(d > 1.0) discard;
    float a = 1.0 - d;
    fragColour = vec4(vCol, a);
}
"""
