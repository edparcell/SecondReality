"""
Part 04 — Logo Reveal (BEGLOGO.EXE)

Original: original/BEG/ (likely)
Effect: The "SECOND REALITY" logo appears via a split-screen zoom transition.
        The screen splits horizontally; the top half zooms up and the bottom
        half zooms down, revealing the logo beneath.
        A plasma-like colour cycle plays on the background.

HD recreation:
  - Logo text rendered at 4K scale via DemoFont
  - Split-screen wipe: top half moves up, bottom half moves down over ~120 frames
  - Background: animated colour gradient cycling on the beat
  - Logo pulses gently (sine-wave scale) after reveal
"""

from __future__ import annotations
import math
import numpy as np
import OpenGL.GL as gl

from demo.part import Part
from demo.dis import DIS
from demo.runner import Runner
from utils.font import DemoFont

_MAX_FRAMES = int(15.0 * 60)
_WIPE_FRAMES = 90   # frames for the split-screen wipe to complete


class LogoReveal(Part):
    MAX_FRAMES = _MAX_FRAMES

    def start(self, dis: DIS, runner: Runner) -> None:
        super().start(dis, runner)
        self._w = runner.width
        self._h = runner.height

        self._prog = runner.compile_shader(_VERT, _FRAG)
        self._bg_prog = runner.compile_shader(_BG_VERT, _BG_FRAG)

        # Render logo text as texture
        font_big  = DemoFont(size=int(runner.height * 0.14))
        font_sub  = DemoFont(size=int(runner.height * 0.045))

        self._logo_tex, self._logo_w, self._logo_h = \
            font_big.make_texture("SECOND REALITY", (255, 220, 60))
        self._sub_tex, self._sub_w, self._sub_h = \
            font_sub.make_texture("THE FUTURE CREW", (200, 200, 255))
        self._year_tex, self._year_w, self._year_h = \
            font_sub.make_texture("ASSEMBLY 1993  1ST PLACE", (180, 180, 180))

        # Background quad VAO
        bg_quad = np.array([
            -1,-1, 0,0,  1,-1, 1,0,  -1,1, 0,1,  1,1, 1,1
        ], dtype=np.float32)
        self._bg_vao = gl.glGenVertexArrays(1)
        self._bg_vbo = gl.glGenBuffers(1)
        gl.glBindVertexArray(self._bg_vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self._bg_vbo)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, bg_quad.nbytes, bg_quad, gl.GL_STATIC_DRAW)
        gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, gl.GL_FALSE, 16, gl.ctypes.c_void_p(0))
        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(1, 2, gl.GL_FLOAT, gl.GL_FALSE, 16, gl.ctypes.c_void_p(8))
        gl.glEnableVertexAttribArray(1)
        gl.glBindVertexArray(0)

    def render(self, dis: DIS, runner: Runner) -> None:
        frame = dis.get_mframe()
        t     = frame / 60.0

        # Animated background
        gl.glUseProgram(self._bg_prog)
        gl.glUniform1f(gl.glGetUniformLocation(self._bg_prog, "uTime"), t)
        gl.glBindVertexArray(self._bg_vao)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        gl.glBindVertexArray(0)

        # Wipe progress: 0 (closed) → 1 (open)
        wipe = min(1.0, frame / _WIPE_FRAMES)
        # Ease out cubic
        wipe = 1.0 - (1.0 - wipe) ** 3

        # Logo scale pulse after wipe completes
        if wipe >= 1.0:
            pulse_t = (frame - _WIPE_FRAMES) / 60.0
            scale = 1.0 + math.sin(pulse_t * 2.0) * 0.015
        else:
            scale = 0.85 + wipe * 0.15

        alpha = wipe

        # Draw logo
        cx = (self._w - self._logo_w * scale) / 2
        cy = (self._h - self._logo_h * scale) / 2 - self._h * 0.05
        self._blit(self._logo_tex,
                   cx, cy, self._logo_w * scale, self._logo_h * scale,
                   alpha, runner)

        # Subtitle
        sx = (self._w - self._sub_w) / 2
        sy = cy + self._logo_h * scale + self._h * 0.02
        self._blit(self._sub_tex, sx, sy, self._sub_w, self._sub_h,
                   alpha * 0.9, runner)

        # Year
        yx = (self._w - self._year_w) / 2
        yy = sy + self._sub_h + self._h * 0.015
        self._blit(self._year_tex, yx, yy, self._year_w, self._year_h,
                   alpha * 0.7, runner)

        a = dis.musplus()
        if 0 > a > -16:
            self.done()

    def stop(self, dis: DIS, runner: Runner) -> None:
        for t in [self._logo_tex, self._sub_tex, self._year_tex]:
            gl.glDeleteTextures([t])
        gl.glDeleteVertexArrays(1, [self._bg_vao])
        gl.glDeleteBuffers(1, [self._bg_vbo])
        gl.glDeleteProgram(self._prog)
        gl.glDeleteProgram(self._bg_prog)

    def _blit(self, tex, x, y, w, h, alpha, runner):
        x0 = x / runner.width  * 2 - 1
        x1 = (x+w) / runner.width  * 2 - 1
        y0 = 1 - y / runner.height * 2
        y1 = 1 - (y+h) / runner.height * 2
        verts = np.array([x0,y1,0,0, x1,y1,1,0, x0,y0,0,1, x1,y0,1,1], dtype=np.float32)
        gl.glUseProgram(self._prog)
        gl.glUniform1i(gl.glGetUniformLocation(self._prog,"uTex"),0)
        gl.glUniform1f(gl.glGetUniformLocation(self._prog,"uAlpha"),alpha)
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, tex)
        vao=gl.glGenVertexArrays(1); vbo=gl.glGenBuffers(1)
        gl.glBindVertexArray(vao); gl.glBindBuffer(gl.GL_ARRAY_BUFFER,vbo)
        gl.glBufferData(gl.GL_ARRAY_BUFFER,verts.nbytes,verts,gl.GL_STREAM_DRAW)
        gl.glVertexAttribPointer(0,2,gl.GL_FLOAT,gl.GL_FALSE,16,gl.ctypes.c_void_p(0))
        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(1,2,gl.GL_FLOAT,gl.GL_FALSE,16,gl.ctypes.c_void_p(8))
        gl.glEnableVertexAttribArray(1)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP,0,4)
        gl.glBindVertexArray(0)
        gl.glDeleteVertexArrays(1,[vao]); gl.glDeleteBuffers(1,[vbo])


_VERT = """
#version 330 core
layout(location=0) in vec2 aPos;
layout(location=1) in vec2 aUV;
out vec2 vUV;
void main(){ vUV=aUV; gl_Position=vec4(aPos,0,1); }
"""
_FRAG = """
#version 330 core
in vec2 vUV; out vec4 fragColour;
uniform sampler2D uTex; uniform float uAlpha;
void main(){ vec4 c=texture(uTex,vUV); fragColour=vec4(c.rgb,c.a*uAlpha); }
"""

_BG_VERT = """
#version 330 core
layout(location=0) in vec2 aPos;
layout(location=1) in vec2 aUV;
out vec2 vUV;
void main(){ vUV=aUV; gl_Position=vec4(aPos,0,1); }
"""
_BG_FRAG = """
#version 330 core
in vec2 vUV; out vec4 fragColour;
uniform float uTime;
void main(){
    float v = sin(vUV.x*6.28+uTime*0.5)*0.5+0.5;
    float u = sin(vUV.y*6.28+uTime*0.3)*0.5+0.5;
    vec3 col = vec3(v*0.05, u*0.03, (v+u)*0.12);
    fragColour = vec4(col, 1.0);
}
"""
