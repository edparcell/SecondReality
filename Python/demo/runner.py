"""
Demo Runner — pygame window, OpenGL context, and main loop.

Manages:
  - pygame / OpenGL initialisation at 3840×2160 (4K) or a scaled fallback
  - The part sequencer: advances through the parts list in order
  - Per-frame: event handling, render, display.flip, DIS.tick()
  - Shared GL state: a fullscreen quad VAO used by shader-based parts
"""

from __future__ import annotations

import os
import sys
import time

import pygame
from pygame.locals import DOUBLEBUF, OPENGL, FULLSCREEN, RESIZABLE

import OpenGL.GL as gl
import numpy as np

from demo.dis import DIS
from demo.music import MusicPlayer
from demo.part import Part


# Default render resolution — can be overridden by environment variable
DEFAULT_WIDTH  = 3840
DEFAULT_HEIGHT = 2160

# Development override: set SECOND_REALITY_WIDTH/HEIGHT to run at lower res
_W = int(os.environ.get("SECOND_REALITY_WIDTH",  DEFAULT_WIDTH))
_H = int(os.environ.get("SECOND_REALITY_HEIGHT", DEFAULT_HEIGHT))


class Runner:
    def __init__(self, parts: list[Part], music_dir: str,
                 width: int = _W, height: int = _H,
                 fullscreen: bool = False) -> None:
        self.width  = width
        self.height = height
        self.aspect = width / height
        self._parts  = parts
        self._part_index = 0
        self._current: Part | None = None

        # Music
        self._music = MusicPlayer(music_dir)

        # DIS
        self.dis = DIS(self._music)

        # Shared GL objects (initialised in run())
        self._quad_vao: int = 0
        self._quad_vbo: int = 0

        self._fullscreen = fullscreen
        self._running = False

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(self) -> None:
        self._init_pygame()
        self._init_gl()
        self._init_music()

        # Start the first part
        self._advance_part()

        self._running = True
        clock = pygame.time.Clock()

        try:
            while self._running:
                self._handle_events()
                if self.dis._exit_requested:
                    break

                # Render current part
                if self._current is not None:
                    self._current.render(self.dis, self)

                pygame.display.flip()
                self.dis.tick()

                # Advance to next part if done
                if self._current is not None and self._current.is_done(self.dis):
                    self._current.stop(self.dis, self)
                    self._part_index += 1
                    if self._part_index >= len(self._parts):
                        break
                    self._advance_part()

                clock.tick(60)
        finally:
            self._shutdown()

    # ------------------------------------------------------------------
    # Helpers available to parts
    # ------------------------------------------------------------------

    def clear(self, r: float = 0.0, g: float = 0.0,
              b: float = 0.0, a: float = 1.0) -> None:
        gl.glClearColor(r, g, b, a)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

    def draw_fullscreen_quad(self) -> None:
        """Draw a [-1,1] NDC quad — used by shader-based fullscreen effects."""
        gl.glBindVertexArray(self._quad_vao)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        gl.glBindVertexArray(0)

    def compile_shader(self, vert_src: str, frag_src: str) -> int:
        """Compile and link a GLSL program.  Returns the program ID."""
        vert = self._compile_stage(vert_src, gl.GL_VERTEX_SHADER)
        frag = self._compile_stage(frag_src, gl.GL_FRAGMENT_SHADER)
        prog = gl.glCreateProgram()
        gl.glAttachShader(prog, vert)
        gl.glAttachShader(prog, frag)
        gl.glLinkProgram(prog)
        if not gl.glGetProgramiv(prog, gl.GL_LINK_STATUS):
            log = gl.glGetProgramInfoLog(prog).decode()
            raise RuntimeError(f"Shader link error:\n{log}")
        gl.glDeleteShader(vert)
        gl.glDeleteShader(frag)
        return prog

    def load_shader_files(self, vert_path: str, frag_path: str) -> int:
        """Load shader sources from files relative to the shaders/ directory."""
        base = os.path.join(os.path.dirname(__file__), '..', 'shaders')
        with open(os.path.join(base, vert_path)) as f:
            vert_src = f.read()
        with open(os.path.join(base, frag_path)) as f:
            frag_src = f.read()
        return self.compile_shader(vert_src, frag_src)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _init_pygame(self) -> None:
        pygame.init()
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
        pygame.display.set_caption("Second Reality HD")

        flags = DOUBLEBUF | OPENGL
        if self._fullscreen:
            flags |= FULLSCREEN

        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
        pygame.display.gl_set_attribute(
            pygame.GL_CONTEXT_PROFILE_MASK,
            pygame.GL_CONTEXT_PROFILE_CORE)
        pygame.display.gl_set_attribute(pygame.GL_DOUBLEBUFFER, 1)
        pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 24)

        pygame.display.set_mode((self.width, self.height), flags)

    def _init_gl(self) -> None:
        gl.glViewport(0, 0, self.width, self.height)
        gl.glClearColor(0.0, 0.0, 0.0, 1.0)
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

        # Build fullscreen quad VAO (positions + UV)
        # Vertex layout: x, y, u, v  (NDC coords, UV 0..1)
        quad = np.array([
            -1.0, -1.0,  0.0, 0.0,
             1.0, -1.0,  1.0, 0.0,
            -1.0,  1.0,  0.0, 1.0,
             1.0,  1.0,  1.0, 1.0,
        ], dtype=np.float32)

        self._quad_vao = gl.glGenVertexArrays(1)
        self._quad_vbo = gl.glGenBuffers(1)

        gl.glBindVertexArray(self._quad_vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self._quad_vbo)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, quad.nbytes, quad, gl.GL_STATIC_DRAW)

        stride = 4 * quad.itemsize
        # attrib 0: position (x, y)
        gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, gl.GL_FALSE, stride,
                                  gl.ctypes.c_void_p(0))
        gl.glEnableVertexAttribArray(0)
        # attrib 1: UV (u, v)
        gl.glVertexAttribPointer(1, 2, gl.GL_FLOAT, gl.GL_FALSE, stride,
                                  gl.ctypes.c_void_p(2 * quad.itemsize))
        gl.glEnableVertexAttribArray(1)

        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        gl.glBindVertexArray(0)

    def _init_music(self) -> None:
        self._music.load(0)
        self._music.play()

    def _advance_part(self) -> None:
        if self._part_index >= len(self._parts):
            return
        self._current = self._parts[self._part_index]
        self._current.start(self.dis, self)

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.dis.request_exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.dis.request_exit()
                elif event.key == pygame.K_RIGHT:
                    # Right arrow skips current part
                    if self._current is not None:
                        self._current.done()

    def _shutdown(self) -> None:
        self._music.stop()
        if self._quad_vao:
            gl.glDeleteVertexArrays(1, [self._quad_vao])
        if self._quad_vbo:
            gl.glDeleteBuffers(1, [self._quad_vbo])
        pygame.quit()

    @staticmethod
    def _compile_stage(src: str, stage: int) -> int:
        shader = gl.glCreateShader(stage)
        gl.glShaderSource(shader, src)
        gl.glCompileShader(shader)
        if not gl.glGetShaderiv(shader, gl.GL_COMPILE_STATUS):
            log = gl.glGetShaderInfoLog(shader).decode()
            stage_name = "vertex" if stage == gl.GL_VERTEX_SHADER else "fragment"
            raise RuntimeError(f"GLSL {stage_name} compile error:\n{log}")
        return shader
