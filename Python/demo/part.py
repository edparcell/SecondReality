"""
Abstract base class for all demo parts.

Each part follows the original DOS pattern:
  - start()    called once before the part runs (load resources, compile shaders)
  - render()   called every frame (draw to the OpenGL framebuffer)
  - is_done()  return True to hand off to the next part
  - stop()     called once after is_done() returns True (free GL resources)

Parts have access to the DIS instance for timing and music sync, and a
reference to the Runner for the screen dimensions and shared GL state.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from demo.dis import DIS
    from demo.runner import Runner


class Part:
    """Base class — subclass and override the four methods below."""

    # Maximum frames before the part forces an exit regardless of music cues.
    # Set to None for parts that rely entirely on music sync.
    MAX_FRAMES: int | None = None

    def __init__(self) -> None:
        self._done: bool = False
        self._start_frame: int = 0

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self, dis: "DIS", runner: "Runner") -> None:
        """One-time initialisation: load textures, compile shaders, etc."""
        self._start_frame = dis.frame
        dis.partstart()

    def render(self, dis: "DIS", runner: "Runner") -> None:
        """Draw one frame.  The GL context is already current.
        Call runner.clear() to clear the framebuffer if needed."""
        pass

    def is_done(self, dis: "DIS") -> bool:
        """Return True to end this part and move to the next."""
        if self._done:
            return True
        if self.MAX_FRAMES is not None:
            if dis.get_mframe() >= self.MAX_FRAMES:
                return True
        return False

    def stop(self, dis: "DIS", runner: "Runner") -> None:
        """Cleanup: delete GL objects, free memory."""
        pass

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def done(self) -> None:
        """Call from render() or a copper callback to signal part end."""
        self._done = True

    def frames_elapsed(self, dis: "DIS") -> int:
        return dis.get_mframe()
