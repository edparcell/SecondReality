"""
Palette utilities.

In the original demo all effects used 256-colour VGA palettes.  In this HD
recreation "palette" means a 256-entry RGB colour table that is passed to
shaders as a uniform sampler1D or used for procedural colour mapping.

A Palette holds 256 × (R, G, B) values in the range [0, 1] (float32).
The original demo stored them as [0, 63] VGA DAC values — we convert on load.
"""

import numpy as np
from typing import Tuple


class Palette:
    def __init__(self, data: np.ndarray | None = None) -> None:
        """data: shape (256, 3) float32 in range [0, 1].  If None, grey ramp."""
        if data is None:
            ramp = np.linspace(0.0, 1.0, 256, dtype=np.float32)
            self.data = np.stack([ramp, ramp, ramp], axis=1)
        else:
            self.data = np.asarray(data, dtype=np.float32)
            assert self.data.shape == (256, 3), "Palette must be (256, 3)"

    @classmethod
    def from_vga(cls, vga_bytes: bytes | np.ndarray) -> "Palette":
        """Construct from 768 VGA DAC bytes (3 bytes per entry, range 0..63)."""
        arr = np.frombuffer(vga_bytes, dtype=np.uint8).reshape(256, 3)
        return cls((arr.astype(np.float32) / 63.0))

    @classmethod
    def black(cls) -> "Palette":
        return cls(np.zeros((256, 3), dtype=np.float32))

    def fade(self, factor: float) -> "Palette":
        """Return a new Palette scaled by factor (0=black, 1=full)."""
        return Palette(np.clip(self.data * factor, 0.0, 1.0))

    def lerp(self, other: "Palette", t: float) -> "Palette":
        """Linear interpolate between this and other (t=0 → self, t=1 → other)."""
        return Palette(self.data * (1 - t) + other.data * t)

    def as_texture_data(self) -> np.ndarray:
        """Return a (1, 256, 3) uint8 array suitable for a 1D GL texture."""
        return (self.data.clip(0, 1) * 255).astype(np.uint8).reshape(1, 256, 3)

    def colour(self, index: int) -> Tuple[float, float, float]:
        r, g, b = self.data[index & 255]
        return float(r), float(g), float(b)


def fire_palette() -> Palette:
    """Classic fire gradient: black → red → yellow → white."""
    data = np.zeros((256, 3), dtype=np.float32)
    for i in range(256):
        t = i / 255.0
        if t < 0.33:
            data[i] = [t * 3, 0, 0]
        elif t < 0.66:
            data[i] = [1.0, (t - 0.33) * 3, 0]
        else:
            data[i] = [1.0, 1.0, (t - 0.66) * 3]
    return Palette(data)


def rainbow_palette(offset: float = 0.0) -> Palette:
    """HSV rainbow cycle."""
    import colorsys
    data = np.zeros((256, 3), dtype=np.float32)
    for i in range(256):
        h = ((i / 256.0) + offset) % 1.0
        r, g, b = colorsys.hsv_to_rgb(h, 1.0, 1.0)
        data[i] = [r, g, b]
    return Palette(data)


def plasma_palette(index: int) -> Palette:
    """Six pre-built plasma palettes matching original/PLZPART/PLZ.C pals[6]."""
    import colorsys
    data = np.zeros((256, 3), dtype=np.float32)
    palettes = [
        # 0: blue-cyan
        lambda i: colorsys.hsv_to_rgb(0.55 + 0.15 * (i/255.0), 1.0, i/255.0),
        # 1: red-orange fire
        lambda i: (min(1.0, i*2/255.0), min(1.0, max(0.0, i*2/255.0 - 0.5)), 0.0),
        # 2: green
        lambda i: (0.0, i/255.0, min(1.0, i*0.5/255.0)),
        # 3: purple-magenta
        lambda i: colorsys.hsv_to_rgb(0.75 + 0.1 * (i/255.0), 1.0, i/255.0),
        # 4: yellow-white
        lambda i: (i/255.0, i/255.0, min(1.0, i*0.5/255.0)),
        # 5: rainbow
        lambda i: colorsys.hsv_to_rgb(i/255.0, 0.9, min(1.0, i*1.5/255.0)),
    ]
    fn = palettes[index % 6]
    for i in range(256):
        rgb = fn(i)
        data[i] = np.clip(rgb, 0.0, 1.0)
    return Palette(data)
