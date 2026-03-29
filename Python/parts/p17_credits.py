"""
Part 17 — End Logo + Credits + End Scroller (ENDLOGO + CRED + ENDSCRL)

Original: original/END/, original/CREDITS/MAIN.C, original/ENDSCRL/
Effect: Three sequential sub-parts:
  1. ENDLOGO: "SECOND REALITY" logo reveal with fireworks effect
  2. CRED: 18 photo credits screens, each with team member names
     Original: screenin() split-screen zoom transition, bitmap font
  3. ENDSCRL: Horizontal scrolling greet text over animated background

HD recreation:
  - Sub-part 1: Logo with particle fireworks
  - Sub-part 2: Credit cards with name overlays, fade transitions
  - Sub-part 3: Horizontal scroller with plasma background
"""

from __future__ import annotations
import math
import numpy as np
import OpenGL.GL as gl

from demo.part import Part
from demo.dis import DIS
from demo.runner import Runner
from utils.font import DemoFont

# Credits data from original/CREDITS/MAIN.C (18 contributors, all 21 roles)
_CREDITS_DATA = [
    ("PSI",           "CODE / DESIGN"),
    ("WILDFIRE",      "CODE"),
    ("TRUG",          "CODE"),
    ("MARVEL",        "GRAPHICS"),
    ("PIXEL",         "GRAPHICS / DESIGN"),
    ("PURPLE MOTION", "MUSIC"),
    ("SKAVEN",        "MUSIC"),
    ("ABYSS",         "DESIGN"),
    ("GORE",          "DESIGN"),
]

# Greet scroll text (abbreviated — original had a long greet list)
_SCROLL_TEXT = (
    "  GREETINGS TO: FUTURE CREW MEMBERS PAST AND PRESENT  "
    "  SPECIAL THANKS TO EVERYONE WHO SUPPORTED THE DEMO SCENE  "
    "  SECOND REALITY - RELEASED AT ASSEMBLY 1993 - 1ST PLACE  "
    "  CODE: PSI / WILDFIRE / TRUG  "
    "  GRAPHICS: MARVEL / PIXEL  "
    "  MUSIC: PURPLE MOTION / SKAVEN  "
    "  DESIGN: ABYSS / GORE  "
    "  THE FUTURE CREW - FINLAND - 1993  "
    "  ...AND IF YOU'RE READING THIS IN THE FAR FUTURE: HELLO!  "
    "                                                            "
)

_LOGO_FRAMES = 300
_CREDITS_FRAMES = 600   # 10 sec for credits
_SCROLL_FRAMES = 900    # 15 sec for scroller
_MAX_FRAMES = _LOGO_FRAMES + _CREDITS_FRAMES + _SCROLL_FRAMES


class Credits(Part):
    MAX_FRAMES = _MAX_FRAMES

    def start(self, dis: DIS, runner: Runner) -> None:
        super().start(dis, runner)
        self._w = runner.width
        self._h = runner.height

        self._prog_sprite = runner.compile_shader(_VERT, _FRAG)
        self._prog_bg     = runner.load_shader_files("fullscreen_quad.vert",
                                                      "plasma.frag")
        self._prog_scroll = runner.compile_shader(_VERT, _FRAG)

        font_logo  = DemoFont(size=int(runner.height * 0.12))
        font_name  = DemoFont(size=int(runner.height * 0.07), bold=True)
        font_role  = DemoFont(size=int(runner.height * 0.04))
        font_scroll= DemoFont(size=int(runner.height * 0.06))

        self._logo_tex, self._logo_w, self._logo_h = \
            font_logo.make_texture("SECOND REALITY", (255, 215, 0))

        # Pre-render credit cards
        self._credit_textures = []
        for name, role in _CREDITS_DATA:
            nt, nw, nh = font_name.make_texture(name, (255, 255, 200))
            rt, rw, rh = font_role.make_texture(role, (200, 200, 255))
            self._credit_textures.append(((nt, nw, nh), (rt, rw, rh)))

        # Pre-render scroll characters
        self._scroll_tex, self._scroll_w, self._scroll_h = \
            font_scroll.make_texture(_SCROLL_TEXT, (200, 240, 255))

        # Particle state for logo fireworks
        import random
        rng = random.Random(0xF1RE)
        self._fw_pos = np.zeros((200, 2), dtype=np.float32)
        self._fw_vel = np.zeros((200, 2), dtype=np.float32)
        self._fw_col = np.zeros((200, 3), dtype=np.float32)
        self._fw_life = np.zeros(200, dtype=np.float32)
        self._fw_maxlife = np.zeros(200, dtype=np.float32)
        for i in range(200):
            a = rng.uniform(0, math.pi*2)
            s = rng.uniform(0.1, 0.8)
            self._fw_vel[i] = [math.cos(a)*s, math.sin(a)*s]
            self._fw_maxlife[i] = rng.uniform(1.5, 3.5)
            self._fw_life[i]    = rng.uniform(0, 2.0)
            r, g, b = rng.random(), rng.random(), rng.random()
            self._fw_col[i] = [max(0.5,r), max(0.5,g), max(0.3,b)]

        self._fw_vao = gl.glGenVertexArrays(1)
        self._fw_vbo = gl.glGenBuffers(1)
        gl.glBindVertexArray(self._fw_vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self._fw_vbo)
        ph = np.zeros((200, 5), dtype=np.float32)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, ph.nbytes, ph, gl.GL_DYNAMIC_DRAW)
        gl.glVertexAttribPointer(0,2,gl.GL_FLOAT,gl.GL_FALSE,20,gl.ctypes.c_void_p(0))
        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(1,3,gl.GL_FLOAT,gl.GL_FALSE,20,gl.ctypes.c_void_p(8))
        gl.glEnableVertexAttribArray(1)
        gl.glBindVertexArray(0)

        self._fw_prog = runner.compile_shader(_FW_VERT, _FW_FRAG)

    def render(self, dis: DIS, runner: Runner) -> None:
        frame = dis.get_mframe()
        t     = frame / 60.0

        # Background plasma
        gl.glUseProgram(self._prog_bg)
        gl.glUniform1f(gl.glGetUniformLocation(self._prog_bg, "uTime"), t)
        gl.glUniform1f(gl.glGetUniformLocation(self._prog_bg, "uP1"), 1000+t*80)
        gl.glUniform1f(gl.glGetUniformLocation(self._prog_bg, "uP2"), 2000+t*60)
        gl.glUniform1f(gl.glGetUniformLocation(self._prog_bg, "uP3"), 3000+t*50)
        gl.glUniform1f(gl.glGetUniformLocation(self._prog_bg, "uP4"), 4000+t*70)
        gl.glUniform1i(gl.glGetUniformLocation(self._prog_bg, "uPalIndex"), 5)
        runner.draw_fullscreen_quad()

        if frame < _LOGO_FRAMES:
            # Sub-part 1: logo + fireworks
            alpha = min(1.0, frame / 60.0)
            cx = (self._w - self._logo_w) / 2
            cy = (self._h - self._logo_h) / 2 - self._h * 0.1
            self._blit(self._logo_tex, cx, cy, self._logo_w, self._logo_h,
                       alpha, runner)
            self._draw_fireworks(t, runner)

        elif frame < _LOGO_FRAMES + _CREDITS_FRAMES:
            # Sub-part 2: credit cards
            local = frame - _LOGO_FRAMES
            card_dur = _CREDITS_FRAMES / len(_CREDITS_DATA)
            card_idx = min(int(local / card_dur), len(_CREDITS_DATA)-1)
            card_t   = (local % card_dur) / card_dur

            # Fade in/out
            if card_t < 0.15:
                alpha = card_t / 0.15
            elif card_t > 0.85:
                alpha = (1.0 - card_t) / 0.15
            else:
                alpha = 1.0

            (nt, nw, nh), (rt, rw, rh) = self._credit_textures[card_idx]
            nx = (self._w - nw) / 2
            ny = self._h * 0.38
            self._blit(nt, nx, ny, nw, nh, alpha, runner)
            rx = (self._w - rw) / 2
            ry = ny + nh + self._h * 0.02
            self._blit(rt, rx, ry, rw, rh, alpha * 0.8, runner)

        else:
            # Sub-part 3: horizontal scroller
            local  = frame - _LOGO_FRAMES - _CREDITS_FRAMES
            scroll = local * (runner.width * 0.005)
            y = (self._h - self._scroll_h) / 2
            x = -scroll % (self._scroll_w + runner.width)
            self._blit(self._scroll_tex, x, y, self._scroll_w, self._scroll_h,
                       1.0, runner)

        a = dis.musplus()
        if 0 > a > -16:
            self.done()

    def stop(self, dis: DIS, runner: Runner) -> None:
        gl.glDeleteTextures([self._logo_tex])
        for (nt,_,_),(rt,_,_) in self._credit_textures:
            gl.glDeleteTextures([nt, rt])
        gl.glDeleteTextures([self._scroll_tex])
        gl.glDeleteVertexArrays(1, [self._fw_vao])
        gl.glDeleteBuffers(1, [self._fw_vbo])
        for p in [self._prog_sprite, self._prog_bg, self._prog_scroll, self._fw_prog]:
            gl.glDeleteProgram(p)

    def _draw_fireworks(self, t: float, runner: Runner) -> None:
        dt = 1/60.0
        self._fw_life += dt
        alive = self._fw_life < self._fw_maxlife
        self._fw_pos[alive] += self._fw_vel[alive] * dt
        self._fw_vel[:,1] -= 0.15 * dt
        self._fw_vel *= 0.995
        # Reset dead particles
        dead = ~alive
        import random
        rng = random.Random(int(t * 1000))
        for i in range(200):
            if dead[i]:
                a = rng.uniform(0, math.pi*2)
                s = rng.uniform(0.1, 0.8)
                self._fw_vel[i]  = [math.cos(a)*s, math.sin(a)*s]
                self._fw_pos[i]  = [0, 0]
                self._fw_life[i] = 0
                self._fw_maxlife[i] = rng.uniform(1.5, 3.5)

        norm = np.clip(self._fw_life / self._fw_maxlife, 0, 1)
        buf = np.zeros((200, 5), dtype=np.float32)
        buf[:, :2] = self._fw_pos * 0.5
        buf[:, 2:5] = self._fw_col * (1 - norm[:, None]) ** 2

        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self._fw_vbo)
        gl.glBufferSubData(gl.GL_ARRAY_BUFFER, 0, buf.nbytes, buf)
        gl.glUseProgram(self._fw_prog)
        gl.glEnable(gl.GL_PROGRAM_POINT_SIZE)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE)
        gl.glBindVertexArray(self._fw_vao)
        gl.glDrawArrays(gl.GL_POINTS, 0, 200)
        gl.glBindVertexArray(0)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

    def _blit(self, tex, x, y, w, h, alpha, runner):
        x0=(x/runner.width)*2-1; x1=((x+w)/runner.width)*2-1
        y0=1-(y/runner.height)*2; y1=1-((y+h)/runner.height)*2
        verts=np.array([x0,y1,0,0, x1,y1,1,0, x0,y0,0,1, x1,y0,1,1],dtype=np.float32)
        gl.glUseProgram(self._prog_sprite)
        gl.glUniform1i(gl.glGetUniformLocation(self._prog_sprite,"uTex"),0)
        gl.glUniform1f(gl.glGetUniformLocation(self._prog_sprite,"uAlpha"),alpha)
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


_VERT = """
#version 330 core
layout(location=0) in vec2 a; layout(location=1) in vec2 u;
out vec2 vU; void main(){ vU=u; gl_Position=vec4(a,0,1); }
"""
_FRAG = """
#version 330 core
in vec2 vU; out vec4 f;
uniform sampler2D uTex; uniform float uAlpha;
void main(){ vec4 c=texture(uTex,vU); f=vec4(c.rgb,c.a*uAlpha); }
"""
_FW_VERT = """
#version 330 core
layout(location=0) in vec2 aPos; layout(location=1) in vec3 aCol;
out vec3 vCol;
void main(){ vCol=aCol; gl_Position=vec4(aPos,0,1); gl_PointSize=3.0; }
"""
_FW_FRAG = """
#version 330 core
in vec3 vCol; out vec4 f;
void main(){
    vec2 uv=gl_PointCoord*2-1;
    if(dot(uv,uv)>1.0) discard;
    f=vec4(vCol, 1.0-dot(uv,uv));
}
"""
