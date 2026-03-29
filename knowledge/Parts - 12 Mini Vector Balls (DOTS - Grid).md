# Part 12: Mini Vector Balls (MINVBALL / GRID)

**Directory:** `original/GRID/`
**Output EXE:** `MINVBALL.EXE`
**Coder:** PSI

---

## Visual Effect

A fountain of small shaded spheres ("vector balls") shoot upward from the centre of the screen, arcing outward under simulated gravity and bouncing off an invisible floor. The balls have depth shading — closer balls are brighter. Eventually the balls settle into a flat grid pattern, then "explode" outward, then fall into place forming different 3D formations. The effect has a playful, bubbly, demo-classic feel.

---

## Technical Implementation

### Source Files

| File | Purpose |
|---|---|
| `MAIN.C` | Main loop: ball physics, animation states |
| `ASM.ASM` | Assembly entry points |
| `DOLINE.C` | Line rasteriser (for grid/floor lines) |
| `LINEBLIT.ASM` | Optimised line blitter |
| `CLINK.INC` | Linker configuration |

### Ball Physics

Each ball has:
- 3D position (x, y, z) in world space
- Velocity vector
- Depth-based colour index

The balls follow parabolic arcs under gravity, bouncing with damping when they hit `y = 0` (floor).

### Grid Lines

The grid floor is rendered using `DOLINE.C` and `LINEBLIT.ASM` — a set of horizontal and vertical lines in perspective projection creating a checkerboard-grid floor plane. `LINEBLIT.ASM` provides the fast per-scanline blitting for the grid lines.

### Transition from Plasma Cube

The plasma cube shrinks to nothing in the centre of the screen. As it disappears, the camera appears to "descend" — the floor grid becomes visible from above, then the balls appear as if the camera is now at ground level.

---

## Surprising Details

- The `GRID/` directory contains the full source for mini vector balls, not a "grid" effect — the name refers to the grid floor that the balls bounce on
- `LINEBLIT.INC` is shared between `GRID/` and `HARD/` (the voxel landscape renderer), suggesting a common library for fast line drawing
