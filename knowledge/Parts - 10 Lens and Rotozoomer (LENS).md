# Part 10: Lens Effect + Rotozoomer (LENS / LNS&ZOOM)

**Directory:** `original/LENS/`
**Output EXE:** `LNS&ZOOM.EXE` (lens and rotozoomer combined into one EXE)
**Coder:** PSI
**Graphics:** Marvel (the source picture)

---

## Visual Effect

This part has three sub-phases:

**Part 1 (Fire wipe):** The screen "ignites" with a fire-curtain wipe effect — two lines of pixels sweep from the centre outward in both directions, revealing the background image line by line.

**Part 2 (Lens bounce):** A circular lens distortion effect bounces around the screen like a ball. The lens magnifies/warps the background image within a circular region, with 3 colour-shifted layers creating a chromatic aberration / stained-glass effect.

**Part 3 (Rotozoomer):** The background image is zoomed and rotated simultaneously (rotozoomer), with the camera orbiting around a focus point with increasing angular velocity, creating a hypnotic spinning/zoom effect. Eventually the image fades to white.

---

## Technical Implementation

### Source Files

| File | Purpose |
|---|---|
| `MAIN.C` | Top-level: initialises data, runs part1/part2/part3 |
| `CALC.C` | Precomputes the lens displacement maps |
| `DOSIN.C` | Sine table generation |
| `ASM.ASM` | Assembly: `dorow`, `dorow2`, `dorow3`, `rotate` routines |

### Lens Displacement Maps

The lens is implemented with **precomputed displacement maps** (`lens1..4`). Each map is a 2D array where each entry gives the screen-space offset to sample from, creating the distortion.

Four separate maps (`lensex0..4`, loaded from binary data embedded in the EXE):
- `lens1` — base displacement table
- `lens2` — 90° phase-shifted version (for colour layer 2)
- `lens3` — another phase (for colour layer 3)
- `lens4` — outer edge mask

The lens is split into a top half and bottom half (processed separately for symmetry efficiency):
```c
for (y = 0; y < lenshig/2; y++) {
    dorow(lens1, u1, y, 0x40);    // colour layer 1 (blue offset palette)
    dorow2(lens2, u1, y, 0x80);   // colour layer 2 (green offset)
    dorow2(lens3, u1, y, 0xC0);   // colour layer 3 (red offset)
    dorow3(lens4, u1, y, 0);       // boundary/mask
}
```

`u1` and `u2` are the screen offsets for the top and bottom halves of the lens respectively. They move with the lens position.

### Bounce Physics (Part 2)

The lens position follows a pre-recorded path stored in `pathdata1[]` (embedded in `lensexp`). This was originally calculated with physics:

```c
// Original physics (with SAVEPATH defined):
x += xa; y += ya;
if (x > 256*64 || x < 60*64) xa = -xa;  // horizontal bounce
if (y > 150*64) {
    y -= ya;
    ya = -ya * 9/10;  // bounce with 90% energy retention
}
ya += 2;  // gravity
```

The final demo uses the pre-recorded path to guarantee the lens stays in-bounds and matches the music timing.

### Rotozoomer (Part 3)

The rotozoomer samples the background image using rotation + scale transform:

```c
// For each screen pixel (sx, sy):
// Sample source image at:
//   src_x = sx * cos(angle) * scale + cx
//   src_y = sx * sin(angle) * scale + cy (etc.)
```

The `rotate()` function (in `ASM.ASM`) takes (x, y, xa, ya) where:
- (x, y) = translation/camera position
- (xa, ya) = rotation direction vector (pre-multiplied by scale)

The camera follows a spiral path stored in `pathdata2[]`:
```c
// Original path computation:
x = 70.0 * sin(d1) - 30;
y = 70.0 * cos(d1) + 60;
d1 -= 0.005;
xa = -1024.0 * sin(d2) * scale;
ya = 1024.0 * cos(d2) * scale;
d2 += d3;  // angular acceleration
```

Scale starts at 2.0 and gradually decreases (zooming out) then increases (zooming in) driven by `scalea`.

### Palette System

The palette has 4 × 64-colour "layers":
- Entries 0–63: base image palette
- Entries 64–127: blue-shifted version (for lens colour layer 1)
- Entries 128–191: green-shifted (layer 2)
- Entries 192–255: red-shifted (layer 3)

Each layer has RGB offsets added to simulate chromatic aberration.

The `fade` buffer contains 64+16 = 80 palette frames for smooth fade transitions.

### The Background Image (`back`)

The background image is loaded from `lensexb` (embedded data). It is a 256×200 cropped version of the Marvel artwork.

For the rotozoomer, a 90°-rotated version is pre-computed:
```c
for (x = 0; x < 256; x++)
    for (y = 0; y < 256; y++)
        rotpic90[x + y*256] = rotpic[y + (255-x)*256];
```

### Assets

| File | Description |
|---|---|
| `LENS.LBM` | The source artwork (256×200 Marvel illustration) |
| `LENSPIC.LBM` | Lens background picture |
| `LENSPIC1.LBM` | Lens background variant |
| `LENSPICX.LBM` | Extended/test version |
| `MONSTER.LBM` | Alternative monster image (test) |

---

## Surprising Details

- The path data was originally computed with physics simulation, then recorded (`SAVEPATH` #define). The recorded path is replayed for the demo to ensure perfect music synchronisation
- The `firfade1[]` / `firfade2[]` arrays control the fire-curtain wipe speeds per scanline — each row has a different `firfade1a[]` velocity, creating the staggered fire sweep
- `lensex0..4` are binary data files embedded via INCBIN — the precomputed lens tables — saving runtime computation time
- The lens uses 4 separate displacement tables (for 4 visual layers), each subtly different, creating chromatic aberration for free
- `SIN4096.INC` provides a 4096-entry sine table (vs the standard `SIN1024.INC`) for the higher precision needed by the rotozoomer camera path
