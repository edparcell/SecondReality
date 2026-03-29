"""
Part 01 — Opening Credits (ALKU.EXE)

Original: original/ALKU/
Effect: Scrolling credits text over an animated starfield.
        Text fades in line by line with a palette-cycle colour effect.
        Ends when music cue fires (~30 seconds in).

HD recreation:
  - Procedural starfield: 800 stars with parallax depth layers
  - Text rendered via DemoFont at 4K scale
  - Palette cycling on text colour driven by musrow()
  - Fade-in/out on part transitions
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


# Credits text matching the original (translated from Finnish to English labels)
_CREDITS = [
    "",
    "THE FUTURE CREW",
    "",
    "PRESENTS",
    "",
    "",
    "SECOND  REALITY",
    "",
    "",
    "CODE",
    "PSI / WILDFIRE / TRUG",
    "",
    "GRAPHICS",
    "MARVEL / PIXEL",
    "",
    "MUSIC",
    "PURPLE MOTION / SKAVEN",
    "",
    "DESIGN",
    "ABYSS / GORE",
    "",
    "ASSEMBLY '93  1ST PLACE",
    "",
    "",
    "PRESS ANY KEY TO SKIP",
]

# Part duration: exit when music cue fires or after MAX_FRAMES at 60fps
_PART_DURATION_SEC = 30.0
_MAX_FRAMES = int(_PART_DURATION_SEC * 60)

# Number of stars in the starfield
_STAR_COUNT = 800


class OpeningCredits(Part):
    MAX_FRAMES = _MAX_FRAMES

    def start(self, dis: DIS, runner: Runner) -> None:
        super().start(dis, runner)
        self._w = runner.width
        self._h = runner.height

        # Compile text-blit shader
        self._prog = runner.compile_shader(_VERT_SRC, _FRAG_SRC)

        # Font sized for 4K (original was ~32px on 200px screen; scale 10.8×)
        self._font = DemoFont(size=int(runner.height * 0.055))

        # Build star field: (x, y, z, speed) all normalised
        rng = random.Random(0x5EC0)
        stars = []
        for _ in range(_STAR_COUNT):
            x = rng.uniform(-1.0, 1.0)
            y = rng.uniform(-1.0, 1.0)
            z = rng.uniform(0.1, 1.0)   # depth (closer = smaller z)
            speed = rng.uniform(0.0003, 0.001) * (1.0 - z + 0.3)
            stars.append((x, y, z, speed))
        self._stars = stars
        self._star_angles = [rng.uniform(0, math.pi * 2) for _ in range(_STAR_COUNT)]

        # Pre-render credit lines as GL textures
        self._line_textures: list[tuple[int, int, int]] = []
        for line in _CREDITS:
            if line.strip():
                colour = (255, 220, 80) if line == "SECOND  REALITY" else \
                         (180, 220, 255) if line in ("THE FUTURE CREW", "PRESENTS") else \
                         (200, 200, 200)
                tex, w, h = self._font.make_texture(line, colour)
                self._line_textures.append((tex, w, h))
            else:
                self._line_textures.append((0, 0, 0))  # blank line

        # Star VBO
        self._star_vao = gl.glGenVertexArrays(1)
        self._star_vbo = gl.glGenBuffers(1)
        gl.glBindVertexArray(self._star_vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self._star_vbo)
        star_data = np.zeros((_STAR_COUNT, 3), dtype=np.float32)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, star_data.nbytes, star_data, gl.GL_DYNAMIC_DRAW)
        gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, gl.GL_FALSE, 12, gl.ctypes.c_void_p(0))
        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(1, 1, gl.GL_FLOAT, gl.GL_FALSE, 12, gl.ctypes.c_void_p(8))
        gl.glEnableVertexAttribArray(1)
        gl.glBindVertexArray(0)

        # Sprite quad VAO (for text blitting)
        self._sprite_prog = runner.compile_shader(_SPRITE_VERT, _SPRITE_FRAG)

    def render(self, dis: DIS, runner: Runner) -> None:
        runner.clear(0.0, 0.0, 0.02)
        frame = dis.get_mframe()
        t = frame / 60.0

        # --- Starfield ---
        self._draw_stars(frame, runner)

        # --- Scrolling credits text ---
        # Scroll speed: move credits up over the duration
        line_h = self._h * 0.075
        scroll_y = self._h - t * line_h * 1.2

        for i, (tex, tw, th) in enumerate(self._line_textures):
            if tex == 0:
                continue
            y = scroll_y + i * line_h
            if y < -th or y > self._h + th:
                continue
            # Fade in as line enters from bottom, fade out at top
            alpha = min(1.0, (self._h - y) / (self._h * 0.15))
            alpha *= min(1.0, (y + th) / (self._h * 0.1))
            alpha = max(0.0, min(1.0, alpha))
            x = (self._w - tw) / 2
            self._blit_texture(tex, x, y, tw, th, alpha, runner)

        # Exit on music cue
        a = dis.musplus()
        if 0 > a > -16:
            self.done()

    def stop(self, dis: DIS, runner: Runner) -> None:
        for tex, _, _ in self._line_textures:
            if tex:
                gl.glDeleteTextures([tex])
        gl.glDeleteVertexArrays(1, [self._star_vao])
        gl.glDeleteBuffers(1, [self._star_vbo])
        gl.glDeleteProgram(self._prog)
        gl.glDeleteProgram(self._sprite_prog)

    # ------------------------------------------------------------------
    def _draw_stars(self, frame: int, runner: Runner) -> None:
        star_data = np.zeros((_STAR_COUNT, 3), dtype=np.float32)
        for i, (sx, sy, sz, speed) in enumerate(self._stars):
            # Stars drift slowly toward viewer (z increases)
            z = (sz + frame * speed) % 1.0
            if z < 0.01:
                z = 0.01
            # Project to screen: closer stars appear further from centre
            px = sx / z
            py = sy / z
            brightness = z * z
            star_data[i] = [px, py, brightness]

        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self._star_vbo)
        gl.glBufferSubData(gl.GL_ARRAY_BUFFER, 0, star_data.nbytes, star_data)

        gl.glUseProgram(self._prog)
        gl.glBindVertexArray(self._star_vao)
        gl.glPointSize(max(1.0, runner.height / 1080.0 * 2.0))
        gl.glDrawArrays(gl.GL_POINTS, 0, _STAR_COUNT)
        gl.glBindVertexArray(0)

    def _blit_texture(self, tex: int, x: float, y: float,
                      w: float, h: float, alpha: float, runner: Runner) -> None:
        # Convert pixel coords to NDC
        x0 = x / runner.width  * 2.0 - 1.0
        x1 = (x + w) / runner.width  * 2.0 - 1.0
        y0 = 1.0 - y / runner.height * 2.0
        y1 = 1.0 - (y + h) / runner.height * 2.0

        verts = np.array([
            x0, y1, 0.0, 0.0,
            x1, y1, 1.0, 0.0,
            x0, y0, 0.0, 1.0,
            x1, y0, 1.0, 1.0,
        ], dtype=np.float32)

        gl.glUseProgram(self._sprite_prog)
        gl.glUniform1i(gl.glGetUniformLocation(self._sprite_prog, "uTex"), 0)
        gl.glUniform1f(gl.glGetUniformLocation(self._sprite_prog, "uAlpha"), alpha)
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, tex)

        vao = gl.glGenVertexArrays(1)
        vbo = gl.glGenBuffers(1)
        gl.glBindVertexArray(vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, verts.nbytes, verts, gl.GL_STREAM_DRAW)
        gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, gl.GL_FALSE, 16, gl.ctypes.c_void_p(0))
        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(1, 2, gl.GL_FLOAT, gl.GL_FALSE, 16, gl.ctypes.c_void_p(8))
        gl.glEnableVertexAttribArray(1)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        gl.glBindVertexArray(0)
        gl.glDeleteVertexArrays(1, [vao])
        gl.glDeleteBuffers(1, [vbo])


# ------------------------------------------------------------------
# Shaders
# ------------------------------------------------------------------

_VERT_SRC = """
#version 330 core
layout(location=0) in vec2 aPos;
layout(location=1) in float aBright;
out float vBright;
void main() {
    vBright = aBright;
    gl_Position = vec4(aPos, 0.0, 1.0);
    gl_PointSize = 2.0;
}
"""

_FRAG_SRC = """
#version 330 core
in float vBright;
out vec4 fragColour;
void main() {
    float b = clamp(vBright, 0.0, 1.0);
    fragColour = vec4(b, b, b * 1.2, 1.0);
}
"""

_SPRITE_VERT = """
#version 330 core
layout(location=0) in vec2 aPos;
layout(location=1) in vec2 aUV;
out vec2 vUV;
void main() {
    vUV = aUV;
    gl_Position = vec4(aPos, 0.0, 1.0);
}
"""

_SPRITE_FRAG = """
#version 330 core
in vec2 vUV;
out vec4 fragColour;
uniform sampler2D uTex;
uniform float uAlpha;
void main() {
    vec4 col = texture(uTex, vUV);
    fragColour = vec4(col.rgb, col.a * uAlpha);
}
"""
