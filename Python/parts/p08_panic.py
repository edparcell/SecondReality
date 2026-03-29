"""
Part 08 — Panic End (PANICEND.EXE)

Original: original/PANIC/ (likely)
Effect: The word "PANIC" fills the screen and colour-cycles rapidly.
        Letters shake/vibrate. Background cycles through saturated colours.
        A brief transitional effect before the forest scroll.

HD recreation:
  - "PANIC" rendered at large scale (fills most of the screen)
  - Rapid hue cycling on text colour (palette rotation)
  - Letters vibrate independently (per-letter offset)
  - Background: dark with pulsing colour
"""

from __future__ import annotations
import math
import random
import numpy as np
import OpenGL.GL as gl

from demo.part import Part
from demo.dis import DIS
from demo.runner import Runner
from utils.font import DemoFont

_MAX_FRAMES = int(8.0 * 60)


class PanicEnd(Part):
    MAX_FRAMES = _MAX_FRAMES

    def start(self, dis: DIS, runner: Runner) -> None:
        super().start(dis, runner)
        self._w = runner.width
        self._h = runner.height

        self._prog = runner.compile_shader(_VERT, _FRAG)
        self._bg_prog = runner.compile_shader(_BG_VERT, _BG_FRAG)

        font = DemoFont(size=int(runner.height * 0.28), bold=True)

        # Pre-render each letter separately for independent shake
        self._letters: list[tuple[int, int, int]] = []
        for ch in "PANIC":
            tex, w, h = font.make_texture(ch, (255, 255, 255))
            self._letters.append((tex, w, h))

        self._bg_vao, self._bg_vbo = self._make_quad()

    def render(self, dis: DIS, runner: Runner) -> None:
        frame = dis.get_mframe()
        t     = frame / 60.0

        # Background: pulsing saturated colour
        import colorsys
        hue = (t * 0.3) % 1.0
        r, g, b = colorsys.hsv_to_rgb(hue, 0.9, 0.2)
        runner.clear(r * 0.3, g * 0.3, b * 0.3)

        # Draw background quad with pulsing colour
        gl.glUseProgram(self._bg_prog)
        gl.glUniform1f(gl.glGetUniformLocation(self._bg_prog, "uTime"), t)
        gl.glBindVertexArray(self._bg_vao)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        gl.glBindVertexArray(0)

        # Draw letters with vibration
        total_w = sum(w for _, w, _ in self._letters)
        start_x = (self._w - total_w) / 2
        max_h   = max(h for _, _, h in self._letters)
        base_y  = (self._h - max_h) / 2

        # Text hue cycling
        import colorsys
        text_hue = (t * 1.5) % 1.0

        for i, (tex, w, h) in enumerate(self._letters):
            # Per-letter vibration
            shake_x = math.sin(t * 12.0 + i * 1.8) * (runner.width * 0.006)
            shake_y = math.cos(t * 9.0  + i * 2.3) * (runner.height * 0.006)

            lh = (text_hue + i * 0.12) % 1.0
            lr, lg, lb = colorsys.hsv_to_rgb(lh, 1.0, 1.0)
            col = (int(lr*255), int(lg*255), int(lb*255))

            x = start_x + shake_x
            y = base_y  + shake_y
            self._blit(tex, x, y, w, h, 1.0, runner, tint=(lr, lg, lb))
            start_x += w

        a = dis.musplus()
        if 0 > a > -16:
            self.done()

    def stop(self, dis: DIS, runner: Runner) -> None:
        for tex, _, _ in self._letters:
            gl.glDeleteTextures([tex])
        gl.glDeleteVertexArrays(1, [self._bg_vao])
        gl.glDeleteBuffers(1, [self._bg_vbo])
        gl.glDeleteProgram(self._prog)
        gl.glDeleteProgram(self._bg_prog)

    def _make_quad(self):
        q = np.array([-1,-1,0,0, 1,-1,1,0, -1,1,0,1, 1,1,1,1], dtype=np.float32)
        vao = gl.glGenVertexArrays(1); vbo = gl.glGenBuffers(1)
        gl.glBindVertexArray(vao); gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, q.nbytes, q, gl.GL_STATIC_DRAW)
        gl.glVertexAttribPointer(0,2,gl.GL_FLOAT,gl.GL_FALSE,16,gl.ctypes.c_void_p(0))
        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(1,2,gl.GL_FLOAT,gl.GL_FALSE,16,gl.ctypes.c_void_p(8))
        gl.glEnableVertexAttribArray(1)
        gl.glBindVertexArray(0)
        return vao, vbo

    def _blit(self, tex, x, y, w, h, alpha, runner, tint=(1,1,1)):
        x0=(x/runner.width)*2-1; x1=((x+w)/runner.width)*2-1
        y0=1-(y/runner.height)*2; y1=1-((y+h)/runner.height)*2
        verts=np.array([x0,y1,0,0, x1,y1,1,0, x0,y0,0,1, x1,y0,1,1],dtype=np.float32)
        gl.glUseProgram(self._prog)
        gl.glUniform1i(gl.glGetUniformLocation(self._prog,"uTex"),0)
        gl.glUniform1f(gl.glGetUniformLocation(self._prog,"uAlpha"),alpha)
        gl.glUniform3f(gl.glGetUniformLocation(self._prog,"uTint"),*tint)
        gl.glActiveTexture(gl.GL_TEXTURE0); gl.glBindTexture(gl.GL_TEXTURE_2D,tex)
        vao=gl.glGenVertexArrays(1); vbo=gl.glGenBuffers(1)
        gl.glBindVertexArray(vao); gl.glBindBuffer(gl.GL_ARRAY_BUFFER,vbo)
        gl.glBufferData(gl.GL_ARRAY_BUFFER,verts.nbytes,verts,gl.GL_STREAM_DRAW)
        gl.glVertexAttribPointer(0,2,gl.GL_FLOAT,gl.GL_FALSE,16,gl.ctypes.c_void_p(0))
        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(1,2,gl.GL_FLOAT,gl.GL_FALSE,16,gl.ctypes.c_void_p(8))
        gl.glEnableVertexAttribArray(1)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP,0,4)
        gl.glBindVertexArray(0); gl.glDeleteVertexArrays(1,[vao]); gl.glDeleteBuffers(1,[vbo])


_VERT  = "#version 330 core\nlayout(location=0)in vec2 a;layout(location=1)in vec2 u;out vec2 vU;void main(){vU=u;gl_Position=vec4(a,0,1);}"
_FRAG  = "#version 330 core\nin vec2 vU;out vec4 f;uniform sampler2D uTex;uniform float uAlpha;uniform vec3 uTint;void main(){vec4 c=texture(uTex,vU);f=vec4(c.rgb*uTint,c.a*uAlpha);}"
_BG_VERT = "#version 330 core\nlayout(location=0)in vec2 a;layout(location=1)in vec2 u;out vec2 vU;void main(){vU=u;gl_Position=vec4(a,0,1);}"
_BG_FRAG = "#version 330 core\nin vec2 vU;out vec4 f;uniform float uTime;void main(){float h=fract(uTime*0.3);vec3 c=vec3(sin(h*6.28)*0.5+0.5,sin(h*6.28+2.1)*0.5+0.5,sin(h*6.28+4.2)*0.5+0.5)*0.15;f=vec4(c,1);}"
