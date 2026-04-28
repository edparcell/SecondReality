"""
DIS - Demo Interrupt Server equivalent.

Mirrors the original DIS API from original/DIS/DIS.H:

  dis_waitb()      -> DIS.waitb()      wait for vsync, return frames since last call
  dis_exit()       -> DIS.exit()       True if ESC pressed
  dis_musplus()    -> DIS.musplus()    music sync code (-ve = running, near 0 = stop cue)
  dis_musrow()     -> DIS.musrow()     current S3M row (0..63)
  dis_setcopper()  -> DIS.set_copper() register per-frame VBlank callback
  dis_setmframe()  -> DIS.set_mframe() reset resettable frame counter
  dis_getmframe()  -> DIS.get_mframe() read resettable frame counter

The copper slots (0..3) are called once per frame after rendering, mirroring
the Amiga-style per-scanline palette effects from the original.
"""

import pygame
from typing import Callable, Optional


class DIS:
    def __init__(self, music):
        self._music = music
        self.frame: int = 0          # total frames since demo start
        self._mframe: int = 0        # resettable music-sync frame counter
        self._mframe_base: int = 0   # frame value when mframe was last reset
        self._copper: list[Optional[Callable]] = [None, None, None, None]
        self._exit_requested: bool = False
        self._last_waitb_frame: int = 0

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def tick(self) -> None:
        """Called once per main-loop iteration (after display.flip).
        Increments frame counter and fires copper callbacks."""
        self.frame += 1
        for cb in self._copper:
            if cb is not None:
                cb()

    def waitb(self) -> int:
        """Wait for the next vertical blank (already done by display.flip).
        Returns the number of frames elapsed since the last call — equivalent
        to the original dis_waitb() repeat count."""
        delta = self.frame - self._last_waitb_frame
        self._last_waitb_frame = self.frame
        return max(1, delta)

    def exit(self) -> bool:
        """Returns True if ESC has been pressed or the window close button used."""
        for event in pygame.event.get(pygame.KEYDOWN):
            if event.key == pygame.K_ESCAPE:
                self._exit_requested = True
        for event in pygame.event.get(pygame.QUIT):
            self._exit_requested = True
        return self._exit_requested

    def request_exit(self) -> None:
        self._exit_requested = True

    # ------------------------------------------------------------------
    # Music sync (mirrors dis_musplus / dis_musrow)
    # ------------------------------------------------------------------

    def musplus(self) -> int:
        """Returns negative value while music is running normally.
        Returns a value in (-16, 0) when a part-exit cue is active.
        Returns 0 when music has stopped entirely.

        Original semantics: parts loop while musplus() not in (-16, 0).
        """
        return self._music.musplus()

    def musrow(self) -> int:
        """Current S3M pattern row (0..63). Used for beat-sync effects."""
        return self._music.musrow()

    # ------------------------------------------------------------------
    # Frame counter (mirrors dis_setmframe / dis_getmframe)
    # ------------------------------------------------------------------

    def set_mframe(self, n: int = 0) -> None:
        """Reset the resettable frame counter to n (typically 0 at part start)."""
        self._mframe_base = self.frame - n
        self._mframe = n

    def get_mframe(self) -> int:
        """Read the resettable frame counter."""
        return self.frame - self._mframe_base

    # ------------------------------------------------------------------
    # Copper callbacks (mirrors dis_setcopper)
    # ------------------------------------------------------------------

    def set_copper(self, slot: int, fn: Optional[Callable]) -> None:
        """Register a per-frame callback in slot 0..3.
        Pass None to clear a slot.  Callbacks are fired by tick()."""
        assert 0 <= slot <= 3
        self._copper[slot] = fn

    # ------------------------------------------------------------------
    # Part lifecycle helpers
    # ------------------------------------------------------------------

    def partstart(self) -> None:
        """Called at the beginning of each part: resets mframe, clears copper."""
        self.set_mframe(0)
        self._copper = [None, None, None, None]
        self._last_waitb_frame = self.frame
