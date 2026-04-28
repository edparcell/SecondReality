"""
Bitmap font renderer.

Mirrors the original 48-character, 32px-tall font from CREDITS/MAIN.C.
Renders text into an OpenGL texture using pygame.font as the HD backend.

Usage:
    font = DemoFont(size=96)          # 96px for 4K (3× original 32px)
    surf = font.render("FUTURE CREW", colour=(255, 200, 0))
    tex = font.surface_to_texture(surf)
    # Use tex in your shader / blit pipeline
"""

import pygame
import numpy as np
import OpenGL.GL as gl
import os


# Character set matching the original: A-Z, 0-9, space, plus some symbols
_CHARSET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,!?:-/()"


class DemoFont:
    def __init__(self, size: int = 96, bold: bool = True) -> None:
        if not pygame.font.get_init():
            pygame.font.init()
        # Use a system monospace font for demo look; fallback to default
        font_candidates = ["couriernew", "courier", "lucidaconsole", "monospace"]
        loaded = None
        for name in font_candidates:
            path = pygame.font.match_font(name, bold=bold)
            if path:
                loaded = pygame.font.Font(path, size)
                break
        self._font = loaded or pygame.font.SysFont("monospace", size, bold=bold)
        self._size = size
        self._cache: dict[tuple, int] = {}  # (text, colour) -> GL texture id

    def render_surface(self, text: str,
                       colour: tuple = (255, 255, 255),
                       bg: tuple | None = None) -> pygame.Surface:
        """Render text to a pygame Surface (RGBA)."""
        antialias = True
        colour_rgb = colour[:3] if len(colour) >= 3 else colour
        surf = self._font.render(text, antialias, colour_rgb,
                                 bg if bg is not None else None)
        return surf.convert_alpha()

    def surface_to_texture(self, surf: pygame.Surface) -> int:
        """Upload a pygame Surface to a GL texture.  Returns texture ID."""
        w, h = surf.get_size()
        data = pygame.image.tostring(surf, "RGBA", True)

        tex = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, tex)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, w, h, 0,
                        gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, data)
        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
        return tex

    def make_texture(self, text: str,
                     colour: tuple = (255, 255, 255)) -> tuple[int, int, int]:
        """Render text and return (texture_id, width_px, height_px)."""
        surf = self.render_surface(text, colour)
        w, h = surf.get_size()
        tex = self.surface_to_texture(surf)
        return tex, w, h

    @staticmethod
    def delete_texture(tex_id: int) -> None:
        gl.glDeleteTextures([tex_id])


def numpy_to_texture(arr: np.ndarray, internal_fmt=gl.GL_RGBA) -> int:
    """Upload a (H, W, 4) uint8 numpy array as an RGBA GL texture."""
    h, w = arr.shape[:2]
    tex = gl.glGenTextures(1)
    gl.glBindTexture(gl.GL_TEXTURE_2D, tex)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_REPEAT)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_REPEAT)
    gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, internal_fmt, w, h, 0,
                    gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, arr.tobytes())
    gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
    return tex
