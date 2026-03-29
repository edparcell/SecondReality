# Part 05: Glenz Vectors (GLENZ)

**Directory:** `original/GLENZ/`
**Output EXE:** `GLENZ.EXE`
**Coder:** PSI

---

## Visual Effect

A semi-transparent polyhedron (a combination of a cube and a rhombicuboctahedron — a cube with extra triangular pyramid "spikes" at each vertex and face) falls from above, bouncing with jelly physics. It rotates continuously with each polygon face rendered as a semi-transparent coloured glass facet (the "glenz" look). The object's colour depends on how many faces are overlapping — faces that point toward the viewer and have two layers appear brighter/lighter, creating a translucent glass effect.

After the first object settles, a second smaller glenz object appears rotating in the opposite direction. Then both animate toward exit.

---

## How Glenz Rendering Works

### The Glenz Effect

"Glenz" (glossy/glass) vectors work by exploiting the VGA palette:
- The 256 palette entries are organised so that each index encodes how many polygon layers have been rendered at that pixel
- When a polygon is drawn, instead of writing a solid colour, it XORs or adds to the existing pixel colour index
- The palette maps low layer-counts to dark colours, higher counts to lighter/brighter colours
- This creates the appearance of semi-transparent, self-illuminated glass

The palette uses a bitfield structure:
- Bits encode which faces are "on top" at each pixel
- The palette LUT maps bit patterns to RGB colours
- Result: overlapping faces add together visually

### Source Files

| File | Purpose |
|---|---|
| `MAIN.C` | Main demo loop: physics, animation states, rendering calls |
| `MAIN1.C` | Alternate/earlier main loop variant |
| `MAINNORM.C` | Normal-mode main (for testing without demo context) |
| `MAINTRAN.C` | Transition-specific main |
| `ASM.ASM` | Main assembly: matrix math, projection, draw |
| `VEC.ASM` | Vector math routines |
| `VECCMD.ASM` | Vector command processing |
| `VID.ASM` | Video output (screen flip, clear) |
| `VIDINIT.ASM` | Video mode initialisation |
| `VIDMISC.ASM` | Miscellaneous video routines |
| `VIDNRM.ASM` | Normal-mode video |
| `VIDPOLY.ASM` | Polygon renderer |
| `VIDTWE.ASM` | Tweaked-mode video |
| `ZOOM.ASM` | Zoom effect (entry/exit zoomer) |
| `MATH.ASM` | Fixed-point arithmetic |
| `NEW.ASM` / `NEW1.ASM` / `NEW2.ASM` | Newer/revised routines |
| `NEWNORM.ASM` | Newer normal-mode routines |
| `ADATA.ASM` | Object geometry data |
| `EDGE.C` | Edge table generation |
| `DOLOOP.C` | Demo loop wrapper |
| `ZOOMER.C` | C-side zoom control |
| `KOE.C` | Test/development experiments |

### Geometry Data (`ADATA.ASM`, `GLENZ/MAIN.C`)

The main object is a 14-vertex solid:
- 8 cube corners at ±ZZZ on each axis
- 6 axis-aligned spike tips at ±170*ZZZ

```
ZZZ = 50
Cube corners: (-100,-100,-100)*ZZZ through (100,100,100)*ZZZ
Spike tips:   (0, 0, ±170)*ZZZ, (±170, 0, 0)*ZZZ, (0, ±170, 0)*ZZZ
```

The triangular faces (`epolys[]`) connect cube edges to spike tips, giving 24 triangular faces total (4 triangles per spike × 6 spikes).

A second smaller companion object (`pointsb[]`) uses `epolysb[]` with alternating colour indices (2-colour pattern).

### Animation / Physics

**Phase 1 (frames 0–640+70): Bounce in**
- `ypos` starts at -9000, falls with `yposa` gravity
- When ypos approaches -300 (ground), velocity reverses with damping
- While bouncing: XYZ scale `xscale/yscale/zscale` modified by `jello` variable
  - Jello squashes the object on impact: `yscale = 120 - jello/30`, `zscale = 120 + jello/30`
  - Jello decays with `jelloa` damping

**Phase 2 (frames 640+70 to 900): Hover**
- Object settles at fixed Y, rotation continues

**Phase 3 (frames 900+): Second object appears**
- `bscale` grows from 0: second glenz object (B) fades in
- Both objects orbit with sinusoidal displacement (`oxp, oyp, ozp`, `oxb, oyb, ozb`)

**Phase 4 (frames 1280+789+): Exit**
- All scales shrink to 0, objects disappear

### Entry Zoomer (`ZOOM.ASM`, `ZOOMER.C`)

Before the main glenz loop, a "zoomer" runs: the background image zooms from small to full-size (a scaling blit). This is the transition from the logo reveal into the glenz part.

The zoomer uses a bounce physics model (similar to the logo part) where the image appears to "slam" down from above and settle.

### Assets

| File | Description |
|---|---|
| `FC.LBM` | Background image used during glenz effect |
| `FCX.LBM` | Alternative background variant |
| `PIC001.LBM` | Secondary picture asset |
| `PIC002.LBM` | Another picture asset |

### Colour/Palette Setup

```c
// Palette: 16 entries, each encoding a face-count (light intensity)
// backpal[16*3] — stored background palette from FC.LBM
// tmppal[768] — full 256-entry palette built from backpal
// Palette entries a>15:
//   b = a & 7 (base colour from first 8)
//   if a & 8: add 16 to each channel (brighter overlay)
```

The copper callback (`copper()`) uploads only the first 16 palette entries each vblank, allowing per-frame palette animation.

---

## Surprising Details

- The `lightshift` variable controls how bright the glenz highlights are — it is literally a bit-shift applied to colour lookup
- The geometry for the second object (`pointsb`) uses `QQQ=99` instead of `ZZZ=50`, making it slightly smaller than the main object
- The `asmtestmode` flag switches to a non-tweaked video mode for development testing
- Multiple commented-out shape transition blocks exist in `MAIN.C` showing iterative exploration of morphing between different vertex positions (the code was commented out before release)
- `HARD/GMAIN.C` is a standalone test harness for the glenz renderer — it runs the same polyhedron in a keyboard-controlled interactive mode (not part of the demo)
- The `_ndebug1` global can enable debug overlays in the renderer
