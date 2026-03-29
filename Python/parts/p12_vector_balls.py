"""
Part 12 — Vector Balls / Mini Vector Balls (MINVBALL.EXE)

Original: original/DOTS/MAIN.C (grid mode) or a separate part
Effect: A 3D grid of metallic/chrome balls rotating and deforming.
        The balls are lit with specular highlights giving a chrome appearance.
        The grid deforms in a wave pattern.

HD recreation:
  - 8×8 grid of spheres (64 balls)
  - Per-sphere Phong shading with strong specular (metallic look)
  - Wave deformation: each ball's position displaced by sin/cos
  - Colour: gradient from blue to cyan with bright specular
"""

from __future__ import annotations
import math
import numpy as np
import OpenGL.GL as gl

from demo.part import Part
from demo.dis import DIS
from demo.runner import Runner
from utils import math3d

_MAX_FRAMES = int(20.0 * 60)
_GRID = 8       # grid is GRID×GRID balls
_BALL_R = 0.18  # ball radius in world units


def _sphere_mesh(radius: float, slices: int = 16, stacks: int = 16):
    """Generate a UV-sphere mesh."""
    verts, norms, idxs = [], [], []
    for i in range(stacks + 1):
        phi = math.pi * i / stacks
        for j in range(slices + 1):
            theta = 2 * math.pi * j / slices
            x = math.sin(phi) * math.cos(theta)
            y = math.cos(phi)
            z = math.sin(phi) * math.sin(theta)
            verts += [x*radius, y*radius, z*radius]
            norms += [x, y, z]
    for i in range(stacks):
        for j in range(slices):
            a = i*(slices+1)+j
            b = a+slices+1
            idxs += [a, b, a+1, b, b+1, a+1]
    return (np.array(verts, dtype=np.float32),
            np.array(norms, dtype=np.float32),
            np.array(idxs, dtype=np.uint32))


class VectorBalls(Part):
    MAX_FRAMES = _MAX_FRAMES

    def start(self, dis: DIS, runner: Runner) -> None:
        super().start(dis, runner)
        self._prog = runner.compile_shader(_VERT, _FRAG)

        verts, norms, idxs = _sphere_mesh(_BALL_R)
        self._index_count = len(idxs)

        self._vao = gl.glGenVertexArrays(1)
        vbo_v, vbo_n, ebo = gl.glGenBuffers(3)
        self._vbos = (vbo_v, vbo_n, ebo)

        gl.glBindVertexArray(self._vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo_v)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, verts.nbytes, verts, gl.GL_STATIC_DRAW)
        gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, 0, None)
        gl.glEnableVertexAttribArray(0)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo_n)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, norms.nbytes, norms, gl.GL_STATIC_DRAW)
        gl.glVertexAttribPointer(1, 3, gl.GL_FLOAT, gl.GL_FALSE, 0, None)
        gl.glEnableVertexAttribArray(1)
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, ebo)
        gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER, idxs.nbytes, idxs, gl.GL_STATIC_DRAW)
        gl.glBindVertexArray(0)

    def render(self, dis: DIS, runner: Runner) -> None:
        runner.clear(0.0, 0.0, 0.05)
        frame = dis.get_mframe()
        t     = frame / 60.0

        proj = math3d.perspective(45.0, runner.width / runner.height, 0.1, 50.0)
        view = math3d.look_at(math3d.vec3(0, 0, 10),
                               math3d.vec3(0, 0, 0),
                               math3d.vec3(0, 1, 0))

        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glUseProgram(self._prog)

        loc_model = gl.glGetUniformLocation(self._prog, "uModel")
        loc_vp    = gl.glGetUniformLocation(self._prog, "uVP")
        loc_light = gl.glGetUniformLocation(self._prog, "uLightDir")
        loc_col   = gl.glGetUniformLocation(self._prog, "uColour")
        loc_time  = gl.glGetUniformLocation(self._prog, "uTime")

        vp = proj @ view
        gl.glUniformMatrix4fv(loc_vp, 1, gl.GL_FALSE, vp.T.flatten())
        gl.glUniform3f(loc_light, 0.5, 0.7, 0.5)
        gl.glUniform1f(loc_time, t)

        gl.glBindVertexArray(self._vao)
        spacing = 0.6
        half    = (_GRID - 1) * spacing / 2

        for gx in range(_GRID):
            for gy in range(_GRID):
                # Wave deformation
                wx = gx * spacing - half
                wy = gy * spacing - half
                wz = math.sin(t * 1.5 + gx * 0.8 + gy * 0.6) * 0.4

                # Colour gradient: blue to cyan based on grid position
                r = 0.1 + gx / _GRID * 0.3
                g = 0.4 + gy / _GRID * 0.4
                b = 0.8

                model = math3d.translation(wx, wy, wz)
                gl.glUniformMatrix4fv(loc_model, 1, gl.GL_FALSE, model.T.flatten())
                gl.glUniform3f(loc_col, r, g, b)
                gl.glDrawElements(gl.GL_TRIANGLES, self._index_count,
                                  gl.GL_UNSIGNED_INT, None)

        gl.glBindVertexArray(0)

        a = dis.musplus()
        if 0 > a > -16:
            self.done()

    def stop(self, dis: DIS, runner: Runner) -> None:
        gl.glDeleteVertexArrays(1, [self._vao])
        gl.glDeleteBuffers(3, list(self._vbos))
        gl.glDeleteProgram(self._prog)


_VERT = """
#version 330 core
layout(location=0) in vec3 aPos;
layout(location=1) in vec3 aNormal;
out vec3 vNormal;
out vec3 vWorldPos;
uniform mat4 uModel;
uniform mat4 uVP;
void main(){
    vec4 wp = uModel * vec4(aPos, 1.0);
    vWorldPos = wp.xyz;
    vNormal = normalize(mat3(uModel) * aNormal);
    gl_Position = uVP * wp;
}
"""

_FRAG = """
#version 330 core
in vec3 vNormal;
in vec3 vWorldPos;
out vec4 fragColour;
uniform vec3 uLightDir;
uniform vec3 uColour;
uniform float uTime;
void main(){
    vec3 N = normalize(vNormal);
    vec3 L = normalize(uLightDir);
    vec3 V = normalize(vec3(0,0,10) - vWorldPos);
    vec3 H = normalize(L + V);
    float diff = max(dot(N, L), 0.0) * 0.7;
    float spec = pow(max(dot(N, H), 0.0), 128.0) * 1.5;
    float ambient = 0.1;
    vec3 col = uColour * (ambient + diff) + vec3(spec);
    fragColour = vec4(col, 1.0);
}
"""
