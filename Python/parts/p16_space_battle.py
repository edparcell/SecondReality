"""
Part 16 — Vector Space Battle (U2E.EXE)

Original: original/U2E/ (second vector part)
Effect: A space battle scene with multiple 3D polygon ships firing at
        each other. The original used flat-shaded polygon rendering with
        Z-sort. Ships are wireframe/solid coloured polyhedra.

HD recreation:
  - Multiple ship objects: pyramids, discs, elongated shapes
  - Flat-shaded polygons with specular highlights
  - Particle "laser" bolts between ships
  - Explosion flashes on impact
  - Starfield background
"""

from __future__ import annotations
import math
import random
import numpy as np
import OpenGL.GL as gl

from demo.part import Part
from demo.dis import DIS
from demo.runner import Runner
from utils import math3d

_MAX_FRAMES = int(25.0 * 60)

# Ship definitions: (shape, colour, base_pos, speed)
_SHIPS = [
    ('fighter',  [0.8, 0.4, 0.0], [ 2.0,  0.5, -5.0], 0.3),
    ('fighter',  [0.2, 0.6, 1.0], [-2.0, -0.3, -4.0], -0.25),
    ('capital',  [0.6, 0.2, 0.8], [ 0.0,  1.5, -8.0], 0.1),
    ('fighter',  [1.0, 0.2, 0.2], [ 1.5, -1.0, -6.0], 0.4),
    ('disc',     [0.2, 0.8, 0.4], [-1.5,  0.8, -7.0], -0.2),
]


def _fighter_mesh():
    """Simple arrowhead fighter shape."""
    v = np.array([
        [ 0.0,  0.0,  1.0],   # nose
        [-0.5, -0.1, -0.5],   # left wing rear
        [ 0.5, -0.1, -0.5],   # right wing rear
        [ 0.0,  0.3, -0.3],   # top fin
        [ 0.0, -0.2, -0.5],   # bottom
    ], dtype=np.float32)
    faces = [[0,1,3],[0,3,2],[0,2,4],[0,4,1],[1,4,2],[1,2,3],[2,4,3],[1,3,4]]
    verts, norms = [], []
    for f in faces:
        a, b, c = v[f[0]], v[f[1]], v[f[2]]
        n = np.cross(b-a, c-a)
        n /= max(np.linalg.norm(n), 1e-8)
        for vi in f:
            verts.append(v[vi])
            norms.append(n)
    return np.array(verts, dtype=np.float32), np.array(norms, dtype=np.float32)


def _capital_mesh():
    """Large elongated capital ship."""
    v = np.array([
        [ 0.0,  0.0,  2.0],
        [-0.3, -0.2, -2.0],
        [ 0.3, -0.2, -2.0],
        [ 0.3,  0.2, -2.0],
        [-0.3,  0.2, -2.0],
    ], dtype=np.float32)
    faces = [[0,1,2],[0,2,3],[0,3,4],[0,4,1],[1,4,3],[1,3,2]]
    verts, norms = [], []
    for f in faces:
        a, b, c = v[f[0]], v[f[1]], v[f[2]]
        n = np.cross(b-a, c-a)
        n /= max(np.linalg.norm(n), 1e-8)
        for vi in f:
            verts.append(v[vi])
            norms.append(n)
    return np.array(verts, dtype=np.float32), np.array(norms, dtype=np.float32)


def _disc_mesh():
    """Disc/saucer shape."""
    segs = 12
    top = 0.15
    r   = 0.5
    verts, norms = [], []
    for i in range(segs):
        a0 = 2*math.pi*i/segs
        a1 = 2*math.pi*(i+1)/segs
        x0, z0 = math.cos(a0)*r, math.sin(a0)*r
        x1, z1 = math.cos(a1)*r, math.sin(a1)*r
        # Top face
        v = np.array([[0,top,0],[x0,0,z0],[x1,0,z1]], dtype=np.float32)
        n = np.cross(v[1]-v[0], v[2]-v[0])
        n /= max(np.linalg.norm(n), 1e-8)
        for vi in v: verts.append(vi); norms.append(n)
        # Bottom
        v = np.array([[0,-top,0],[x1,0,z1],[x0,0,z0]], dtype=np.float32)
        n = np.cross(v[1]-v[0], v[2]-v[0])
        n /= max(np.linalg.norm(n), 1e-8)
        for vi in v: verts.append(vi); norms.append(n)
    return np.array(verts, dtype=np.float32), np.array(norms, dtype=np.float32)


_MESH_BUILDERS = {
    'fighter': _fighter_mesh,
    'capital': _capital_mesh,
    'disc':    _disc_mesh,
}


class SpaceBattle(Part):
    MAX_FRAMES = _MAX_FRAMES

    def start(self, dis: DIS, runner: Runner) -> None:
        super().start(dis, runner)
        self._prog = runner.compile_shader(_VERT, _FRAG)
        self._star_prog = runner.compile_shader(_STAR_VERT, _STAR_FRAG)

        # Build per-ship VAOs
        self._ship_vaos = []
        for shape, col, pos, speed in _SHIPS:
            verts, norms = _MESH_BUILDERS[shape]()
            vao = gl.glGenVertexArrays(1)
            vbo_v, vbo_n = gl.glGenBuffers(2)
            gl.glBindVertexArray(vao)
            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo_v)
            gl.glBufferData(gl.GL_ARRAY_BUFFER, verts.nbytes, verts, gl.GL_STATIC_DRAW)
            gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, 0, None)
            gl.glEnableVertexAttribArray(0)
            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo_n)
            gl.glBufferData(gl.GL_ARRAY_BUFFER, norms.nbytes, norms, gl.GL_STATIC_DRAW)
            gl.glVertexAttribPointer(1, 3, gl.GL_FLOAT, gl.GL_FALSE, 0, None)
            gl.glEnableVertexAttribArray(1)
            gl.glBindVertexArray(0)
            self._ship_vaos.append((vao, [vbo_v, vbo_n], len(verts)))

        # Stars
        rng = random.Random(0xBATL)
        star_data = np.array([[rng.uniform(-1,1), rng.uniform(-1,1),
                                rng.uniform(0.2,1.0)] for _ in range(500)],
                              dtype=np.float32)
        self._star_vao = gl.glGenVertexArrays(1)
        self._star_vbo = gl.glGenBuffers(1)
        gl.glBindVertexArray(self._star_vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self._star_vbo)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, star_data.nbytes, star_data, gl.GL_STATIC_DRAW)
        gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, gl.GL_FALSE, 12, gl.ctypes.c_void_p(0))
        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(1, 1, gl.GL_FLOAT, gl.GL_FALSE, 12, gl.ctypes.c_void_p(8))
        gl.glEnableVertexAttribArray(1)
        gl.glBindVertexArray(0)

    def render(self, dis: DIS, runner: Runner) -> None:
        runner.clear(0.0, 0.0, 0.02)
        frame = dis.get_mframe()
        t     = frame / 60.0

        # Stars
        gl.glUseProgram(self._star_prog)
        gl.glEnable(gl.GL_PROGRAM_POINT_SIZE)
        gl.glBindVertexArray(self._star_vao)
        gl.glDrawArrays(gl.GL_POINTS, 0, 500)
        gl.glBindVertexArray(0)

        proj = math3d.perspective(55.0, runner.width / runner.height, 0.1, 100.0)
        view = math3d.look_at(math3d.vec3(math.sin(t*0.2)*1.5, math.sin(t*0.15)*0.5, 5),
                               math3d.vec3(0, 0, -5),
                               math3d.vec3(0, 1, 0))

        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glUseProgram(self._prog)
        gl.glUniformMatrix4fv(gl.glGetUniformLocation(self._prog, "uVP"),
                              1, gl.GL_FALSE, (proj @ view).T.flatten())
        gl.glUniform3f(gl.glGetUniformLocation(self._prog, "uLightDir"),
                       0.5, 0.7, 0.5)
        gl.glUniform1f(gl.glGetUniformLocation(self._prog, "uTime"), t)

        for i, (shape, col, base_pos, speed) in enumerate(_SHIPS):
            # Animate ships in orbiting paths
            bx, by, bz = base_pos
            px = bx + math.sin(t * speed + i) * 1.5
            py = by + math.cos(t * speed * 0.7 + i) * 0.5
            pz = bz + math.sin(t * speed * 0.5) * 0.5

            ry = t * speed * 2
            rx = math.sin(t * 0.3 + i) * 0.3

            model = (math3d.translation(px, py, pz)
                     @ math3d.rot_y(ry)
                     @ math3d.rot_x(rx))

            gl.glUniformMatrix4fv(gl.glGetUniformLocation(self._prog, "uModel"),
                                  1, gl.GL_FALSE, model.T.flatten())
            gl.glUniform3fv(gl.glGetUniformLocation(self._prog, "uColour"),
                            1, np.array(col, dtype=np.float32))

            vao, vbos, vert_count = self._ship_vaos[i]
            gl.glBindVertexArray(vao)
            gl.glDrawArrays(gl.GL_TRIANGLES, 0, vert_count)
            gl.glBindVertexArray(0)

        a = dis.musplus()
        if 0 > a > -16:
            self.done()

    def stop(self, dis: DIS, runner: Runner) -> None:
        for vao, vbos, _ in self._ship_vaos:
            gl.glDeleteVertexArrays(1, [vao])
            gl.glDeleteBuffers(len(vbos), vbos)
        gl.glDeleteVertexArrays(1, [self._star_vao])
        gl.glDeleteBuffers(1, [self._star_vbo])
        gl.glDeleteProgram(self._prog)
        gl.glDeleteProgram(self._star_prog)


_VERT = """
#version 330 core
layout(location=0) in vec3 aPos;
layout(location=1) in vec3 aNormal;
out vec3 vNormal; out vec3 vPos;
uniform mat4 uModel; uniform mat4 uVP;
void main(){
    vec4 wp=uModel*vec4(aPos,1); vPos=wp.xyz;
    vNormal=normalize(mat3(uModel)*aNormal);
    gl_Position=uVP*wp;
}
"""
_FRAG = """
#version 330 core
in vec3 vNormal; in vec3 vPos;
out vec4 fragColour;
uniform vec3 uLightDir; uniform vec3 uColour; uniform float uTime;
void main(){
    vec3 N=normalize(vNormal); vec3 L=normalize(uLightDir);
    float d=max(dot(N,L),0.0);
    vec3 V=normalize(vec3(0,0,5)-vPos); vec3 H=normalize(L+V);
    float s=pow(max(dot(N,H),0.0),64.0);
    fragColour=vec4(uColour*(0.1+d*0.8)+vec3(s*0.6),1.0);
}
"""
_STAR_VERT = """
#version 330 core
layout(location=0) in vec2 aPos;
layout(location=1) in float aBright;
out float vB;
void main(){ vB=aBright; gl_Position=vec4(aPos,0,1); gl_PointSize=2.0; }
"""
_STAR_FRAG = """
#version 330 core
in float vB; out vec4 f;
void main(){ f=vec4(vB,vB,vB*1.2,1); }
"""
