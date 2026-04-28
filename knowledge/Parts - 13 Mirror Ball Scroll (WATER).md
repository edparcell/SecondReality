# Part 13: Mirror Ball Scroll / Raytraced Scroll (WATER / RAYSCRL)

**Directory:** `original/WATER/`
**Output EXE:** `RAYSCRL.EXE`
**Coder:** TRUG

---

## Visual Effect

A raytraced reflective sphere (mirror ball) sits above a checkerboard floor that scrolls text. The sphere reflects the environment around it. Text scrolls past on the floor reading "we have something to say..." or similar message. The effect demonstrates a static pre-rendered sphere combined with a dynamic scrolling background.

The sphere reflection is pre-calculated (not real-time raytracing) — the sphere's reflection map is baked and then composited with the moving background.

---

## Technical Implementation

### Source Files

| File | Purpose |
|---|---|
| `ROUTINES.ASM` | Sprite compositing routine (same pattern as FOREST) |

The `Putrouts1` routine (PASCAL FAR calling convention) composites the scroll font over the background:
- If font pixel non-zero: write font pixel
- If font pixel zero: write background pixel

This is identical to the FOREST scroll compositing technique.

### Configuration/Data Files (`*.INC`)

These `.INC` files define the raytracing scene parameters baked at development time:

| File | Purpose |
|---|---|
| `COLORS.INC` | Colour palette definitions for the scene |
| `FOV.INC` | Field-of-view parameters |
| `IOR.INC` | Index of refraction (for glass/mirror calculations) |
| `LIZARD.INC` | Texture map (lizard/checkerboard skin pattern) |
| `MARBLE.INC` | Marble texture map |
| `SHAPES.INC` | Scene shape definitions (sphere geometry) |
| `SHAPES2.INC` | Additional shape data |
| `STEM1.INC` | Stem/stand geometry for the sphere |
| `WORLD12.INC` | World/environment data |

### Pre-Computation

The sphere's reflection lookup table was pre-computed using a raytracer (likely custom-written for this effect). The raytrace traced rays from each pixel on screen, reflecting them off the sphere surface, and recording what background colour would be visible in the reflection.

This lookup table is then used at runtime to composite the sphere over the moving background.

### Background Scrolling

The checkerboard/text floor uses the same run-length encoded sprite position approach as the FOREST and TUNNELI sections. The CRTC start address is adjusted each frame to scroll the background.

### Assets

| File | Description |
|---|---|
| `FINAL.LBM` | Final rendered scene with sphere |
| `FINAL2.LBM` | Alternative final scene |
| `FONA.LBM` | Font for the scroll text |
| `KOE.LBM` | Test/development image |
| `LOGO.LBM` | Logo for display |
| `SWORD.LBM` | Sword graphic (possibly props in scene) |
| `TAUSTA.LBM` | Background image (tausta = Finnish for "background") |

---

## Surprising Details

- The `.INC` scene description files in `WATER/` suggest TRUG wrote a custom raytracer to generate the sphere reflection map
- `IOR.INC` (index of refraction) suggests the sphere was modelled as a glass/crystal ball, not just a mirror — with refraction as well as reflection
- The `LIZARD.INC` and `MARBLE.INC` texture names suggest the floor had procedural textures
- The script calls this "Raytrace Scroll — water sinus and mirror ball + scroller"  — implying there may also be a water-wave distortion applied to the background
- The `WATER/` directory name (vs the effect's visual description) likely reflects that the floor was a water-ripple effect rather than a static checkerboard in an earlier design
