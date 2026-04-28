"""
Part 03 — Explosion Animation (PAM.EXE)

Original: original/PAM/
Effect: An FLI delta-compressed animation of an explosion, played back
        from ANIM.FLI.  The original used a custom FLI packer with
        delta compression and 16-byte frame alignment.

HD recreation:
  - Procedural particle explosion (no FLI file — redrawn)
  - 2000 particles with physics: velocity, gravity, drag, fade
  - Bright orange/yellow/white colour gradient by age
  - Shockwave ring expanding outward
  - Smoke: slow grey particles that linger and rise
"""

from __future__ import annotations
import math
import random
import numpy as np
import OpenGL.GL as gl

from demo.part import Part
from demo.dis import DIS
from demo.runner import Runner

_MAX_FRAMES = int(8.0 * 60)
_PARTICLE_COUNT = 2000
_SMOKE_COUNT = 400


class Explosion(Part):
    MAX_FRAMES = _MAX_FRAMES

    def start(self, dis: DIS, runner: Runner) -> None:
        super().start(dis, runner)

        self._prog_particles = runner.compile_shader(_VERT_P, _FRAG_P)
        self._prog_shockwave  = runner.compile_shader(_VERT_S, _FRAG_S)

        rng = random.Random(0xB00M)

        # Fire particles
        self._pos  = np.zeros((_PARTICLE_COUNT, 2), dtype=np.float32)
        self._vel  = np.zeros((_PARTICLE_COUNT, 2), dtype=np.float32)
        self._life = np.zeros(_PARTICLE_COUNT, dtype=np.float32)
        self._maxlife = np.zeros(_PARTICLE_COUNT, dtype=np.float32)
        for i in range(_PARTICLE_COUNT):
            angle = rng.uniform(0, math.pi * 2)
            speed = rng.uniform(0.2, 1.8) * rng.uniform(0.5, 1.0)
            self._vel[i]     = [math.cos(angle) * speed, math.sin(angle) * speed]
            self._maxlife[i] = rng.uniform(1.5, 4.0)
            self._life[i]    = rng.uniform(0.0, 0.5)  # stagger start

        # Smoke particles
        self._smoke_pos  = np.zeros((_SMOKE_COUNT, 2), dtype=np.float32)
        self._smoke_vel  = np.zeros((_SMOKE_COUNT, 2), dtype=np.float32)
        self._smoke_life = np.zeros(_SMOKE_COUNT, dtype=np.float32)
        for i in range(_SMOKE_COUNT):
            angle = rng.uniform(0, math.pi * 2)
            speed = rng.uniform(0.05, 0.3)
            self._smoke_vel[i]  = [math.cos(angle)*speed, math.sin(angle)*speed + 0.05]
            self._smoke_life[i] = rng.uniform(0.3, 0.8)  # delayed start

        # VAO for particles
        self._vao = gl.glGenVertexArrays(1)
        self._vbo = gl.glGenBuffers(1)
        gl.glBindVertexArray(self._vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self._vbo)
        placeholder = np.zeros((_PARTICLE_COUNT, 3), dtype=np.float32)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, placeholder.nbytes, placeholder, gl.GL_DYNAMIC_DRAW)
        gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, gl.GL_FALSE, 12, gl.ctypes.c_void_p(0))
        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(1, 1, gl.GL_FLOAT, gl.GL_FALSE, 12, gl.ctypes.c_void_p(8))
        gl.glEnableVertexAttribArray(1)
        gl.glBindVertexArray(0)

        self._shockwave_vao = gl.glGenVertexArrays(1)
        self._shockwave_vbo = gl.glGenBuffers(1)
        segs = 128
        angles = np.linspace(0, math.pi * 2, segs, endpoint=False, dtype=np.float32)
        ring = np.column_stack([np.cos(angles), np.sin(angles)])
        gl.glBindVertexArray(self._shockwave_vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self._shockwave_vbo)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, ring.nbytes, ring, gl.GL_STATIC_DRAW)
        gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, gl.GL_FALSE, 0, None)
        gl.glEnableVertexAttribArray(0)
        gl.glBindVertexArray(0)
        self._ring_segs = segs

    def render(self, dis: DIS, runner: Runner) -> None:
        runner.clear(0.0, 0.0, 0.0)
        frame = dis.get_mframe()
        dt    = 1.0 / 60.0
        t     = frame * dt
        aspect = runner.width / runner.height

        # Update particles
        alive_mask = self._life < self._maxlife
        self._life[alive_mask] += dt
        self._pos[alive_mask] += self._vel[alive_mask] * dt
        # Gravity and drag
        self._vel[:, 1] -= 0.3 * dt   # gravity
        self._vel        *= 0.992      # drag

        # Build draw buffer: [x, y, age_norm]  (x,y in NDC-like -1..1)
        buf = np.zeros((_PARTICLE_COUNT, 3), dtype=np.float32)
        norm = np.clip(self._life / self._maxlife, 0.0, 1.0)
        buf[:, 0] = self._pos[:, 0] * 0.6 / aspect
        buf[:, 1] = self._pos[:, 1] * 0.6
        buf[:, 2] = norm

        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self._vbo)
        gl.glBufferSubData(gl.GL_ARRAY_BUFFER, 0, buf.nbytes, buf)

        gl.glUseProgram(self._prog_particles)
        gl.glUniform1f(gl.glGetUniformLocation(self._prog_particles, "uTime"), t)
        gl.glEnable(gl.GL_PROGRAM_POINT_SIZE)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE)  # additive for fire glow
        gl.glBindVertexArray(self._vao)
        gl.glDrawArrays(gl.GL_POINTS, 0, _PARTICLE_COUNT)
        gl.glBindVertexArray(0)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

        # Shockwave ring
        if t < 1.5:
            radius = t * 0.6
            alpha  = max(0.0, 1.0 - t / 1.5)
            gl.glUseProgram(self._prog_shockwave)
            gl.glUniform1f(gl.glGetUniformLocation(self._prog_shockwave, "uRadius"), radius / aspect)
            gl.glUniform1f(gl.glGetUniformLocation(self._prog_shockwave, "uAlpha"),  alpha)
            gl.glUniform1f(gl.glGetUniformLocation(self._prog_shockwave, "uAspect"), aspect)
            gl.glEnable(gl.GL_BLEND)
            gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE)
            gl.glBindVertexArray(self._shockwave_vao)
            gl.glLineWidth(max(1.0, runner.height / 600.0))
            gl.glDrawArrays(gl.GL_LINE_LOOP, 0, self._ring_segs)
            gl.glBindVertexArray(0)
            gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

        if dis.get_mframe() >= _MAX_FRAMES:
            self.done()
        a = dis.musplus()
        if 0 > a > -16:
            self.done()

    def stop(self, dis: DIS, runner: Runner) -> None:
        gl.glDeleteVertexArrays(1, [self._vao])
        gl.glDeleteBuffers(1, [self._vbo])
        gl.glDeleteVertexArrays(1, [self._shockwave_vao])
        gl.glDeleteBuffers(1, [self._shockwave_vbo])
        gl.glDeleteProgram(self._prog_particles)
        gl.glDeleteProgram(self._prog_shockwave)


_VERT_P = """
#version 330 core
layout(location=0) in vec2 aPos;
layout(location=1) in float aAge;
out float vAge;
void main() {
    vAge = aAge;
    gl_Position = vec4(aPos, 0.0, 1.0);
    gl_PointSize = mix(6.0, 1.5, aAge);
}
"""

_FRAG_P = """
#version 330 core
in float vAge;
out vec4 fragColour;
uniform float uTime;
void main() {
    // Fire colour gradient: white→yellow→orange→red→transparent
    float t = vAge;
    vec3 col;
    if (t < 0.2)      col = mix(vec3(1.0,1.0,1.0), vec3(1.0,1.0,0.3), t/0.2);
    else if (t < 0.5) col = mix(vec3(1.0,1.0,0.3), vec3(1.0,0.5,0.0), (t-0.2)/0.3);
    else               col = mix(vec3(1.0,0.5,0.0), vec3(0.4,0.0,0.0), (t-0.5)/0.5);
    float alpha = (1.0 - t) * (1.0 - t);
    fragColour = vec4(col, alpha);
}
"""

_VERT_S = """
#version 330 core
layout(location=0) in vec2 aDir;
uniform float uRadius;
uniform float uAspect;
void main() {
    gl_Position = vec4(aDir.x * uRadius, aDir.y * uRadius * uAspect, 0.0, 1.0);
}
"""

_FRAG_S = """
#version 330 core
out vec4 fragColour;
uniform float uAlpha;
void main() {
    fragColour = vec4(1.0, 0.7, 0.3, uAlpha);
}
"""
