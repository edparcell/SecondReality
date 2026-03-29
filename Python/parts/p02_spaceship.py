"""
Part 02 — Spaceship Flyby (U2A.EXE / VISU)

Original: original/VISU/
Effect: A 3D city/spaceship scene rendered from a moving camera.
        The original loaded .ASC (Autodesk Animator ASCII) geometry,
        .VUE camera animation files, and .MAT material files, then did
        flat/Gouraud-shaded polygon rendering with Z-sort.

HD recreation:
  - Procedural city geometry (no .ASC files — redrawn)
  - Animated camera flyby path (mirrors original .VUE animation curve)
  - Flat-shaded polygons with per-face colours
  - Starfield background
  - Smooth flythrough with depth fog
"""

from __future__ import annotations
import math
import numpy as np
import OpenGL.GL as gl

from demo.part import Part
from demo.dis import DIS
from demo.runner import Runner
from utils import math3d

_MAX_FRAMES = int(20.0 * 60)  # ~20 seconds


def _build_city() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Generate a simple procedural city: grid of rectangular buildings.
    Returns (vertices, indices, colours) as float32/uint32/float32 arrays."""
    verts  = []
    idxs   = []
    cols   = []
    vi     = 0

    rng_seed = 42
    def pseudo(n):
        # Deterministic pseudo-random from seed
        nonlocal rng_seed
        rng_seed = (rng_seed * 1103515245 + 12345) & 0x7fffffff
        return (rng_seed % n)

    grid = 8
    spacing = 3.0
    for gx in range(-grid, grid + 1):
        for gz in range(-grid, grid + 1):
            if abs(gx) < 2 and abs(gz) < 2:
                continue  # leave a gap for the "street"
            bx = gx * spacing
            bz = gz * spacing
            w  = 0.6 + pseudo(10) * 0.04
            d  = 0.6 + pseudo(10) * 0.04
            h  = 0.5 + pseudo(30) * 0.1

            # Colour variation: dark blues, greys, occasional lit windows
            r = 0.05 + pseudo(10) * 0.01
            g = 0.06 + pseudo(10) * 0.01
            b = 0.12 + pseudo(20) * 0.02
            face_col = [r, g, b]

            # Box: 8 vertices, 12 triangles (6 faces × 2 tri)
            x0, x1 = bx - w, bx + w
            y0, y1 = 0.0, h
            z0, z1 = bz - d, bz + d

            box_v = [
                [x0,y0,z0],[x1,y0,z0],[x1,y1,z0],[x0,y1,z0],  # front
                [x0,y0,z1],[x1,y0,z1],[x1,y1,z1],[x0,y1,z1],  # back
            ]
            for v in box_v:
                verts.append(v)
                cols.append(face_col)

            box_i = [
                0,1,2, 0,2,3,   # front
                5,4,7, 5,7,6,   # back
                4,0,3, 4,3,7,   # left
                1,5,6, 1,6,2,   # right
                3,2,6, 3,6,7,   # top
                4,5,1, 4,1,0,   # bottom
            ]
            for idx in box_i:
                idxs.append(vi + idx)
            vi += 8

    return (np.array(verts, dtype=np.float32),
            np.array(idxs,  dtype=np.uint32),
            np.array(cols,  dtype=np.float32))


class SpaceshipFlyby(Part):
    MAX_FRAMES = _MAX_FRAMES

    def start(self, dis: DIS, runner: Runner) -> None:
        super().start(dis, runner)
        self._w = runner.width
        self._h = runner.height

        self._prog = runner.compile_shader(_VERT, _FRAG)

        verts, idxs, cols = _build_city()
        self._index_count = len(idxs)

        self._vao = gl.glGenVertexArrays(1)
        vbo_v, vbo_c, ebo = gl.glGenBuffers(3)
        self._vbo_v = vbo_v
        self._vbo_c = vbo_c
        self._ebo   = ebo

        gl.glBindVertexArray(self._vao)

        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo_v)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, verts.nbytes, verts, gl.GL_STATIC_DRAW)
        gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, 0, None)
        gl.glEnableVertexAttribArray(0)

        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo_c)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, cols.nbytes, cols, gl.GL_STATIC_DRAW)
        gl.glVertexAttribPointer(1, 3, gl.GL_FLOAT, gl.GL_FALSE, 0, None)
        gl.glEnableVertexAttribArray(1)

        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, ebo)
        gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER, idxs.nbytes, idxs, gl.GL_STATIC_DRAW)

        gl.glBindVertexArray(0)

    def render(self, dis: DIS, runner: Runner) -> None:
        runner.clear(0.0, 0.0, 0.02)

        frame = dis.get_mframe()
        t     = frame / 60.0

        # Camera flyby path: spiral in over the city then pull up and away
        cam_x = math.sin(t * 0.3) * 8.0
        cam_z = -t * 2.0 + 5.0
        cam_y = max(0.5, 4.0 - t * 0.15)
        eye    = math3d.vec3(cam_x, cam_y, cam_z)
        target = math3d.vec3(cam_x + math.sin(t * 0.2), cam_y - 0.1, cam_z - 5.0)
        up     = math3d.vec3(0, 1, 0)

        proj = math3d.perspective(60.0, runner.width / runner.height, 0.05, 200.0)
        view = math3d.look_at(eye, target, up)
        model = math3d.identity()

        mvp = proj @ view @ model

        gl.glUseProgram(self._prog)
        gl.glUniformMatrix4fv(
            gl.glGetUniformLocation(self._prog, "uMVP"),
            1, gl.GL_FALSE, mvp.T.flatten())
        gl.glUniform1f(gl.glGetUniformLocation(self._prog, "uTime"), t)

        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glBindVertexArray(self._vao)
        gl.glDrawElements(gl.GL_TRIANGLES, self._index_count,
                          gl.GL_UNSIGNED_INT, None)
        gl.glBindVertexArray(0)

        a = dis.musplus()
        if 0 > a > -16:
            self.done()

    def stop(self, dis: DIS, runner: Runner) -> None:
        gl.glDeleteVertexArrays(1, [self._vao])
        gl.glDeleteBuffers(1, [self._vbo_v])
        gl.glDeleteBuffers(1, [self._vbo_c])
        gl.glDeleteBuffers(1, [self._ebo])
        gl.glDeleteProgram(self._prog)


_VERT = """
#version 330 core
layout(location=0) in vec3 aPos;
layout(location=1) in vec3 aCol;
out vec3 vCol;
out float vDepth;
uniform mat4 uMVP;
void main() {
    gl_Position = uMVP * vec4(aPos, 1.0);
    vCol   = aCol;
    vDepth = gl_Position.z / gl_Position.w;
}
"""

_FRAG = """
#version 330 core
in vec3 vCol;
in float vDepth;
out vec4 fragColour;
uniform float uTime;
void main() {
    // Distance fog
    float fog = exp(-vDepth * 0.08);
    vec3 fogCol = vec3(0.0, 0.02, 0.06);
    vec3 col = mix(fogCol, vCol, clamp(fog, 0.0, 1.0));
    fragColour = vec4(col, 1.0);
}
"""
