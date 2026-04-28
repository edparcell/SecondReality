# Part 14: 3D Sinus Field / Comanche-Style Voxel Landscape (HARD / 3DSINFLD)

**Directory:** `original/HARD/`
**Output EXE:** `3DSINFLD.EXE`
**Coder:** PSI

---

## Visual Effect

A 3D undulating landscape (height map) rendered in a style reminiscent of the Comanche helicopter game (1992, NovaLogic). The landscape is made of a sinusoidal height field — every point on a 2D grid has its height determined by a sum of sine waves, creating smooth rolling hills or ocean waves. The camera swoops over/through the landscape. At the end, the camera rises and the landscape fades to black.

The SCRIPT describes this as: "Comanche = 3D sinus field — fade from ? blue effect — undulating desert/ocean surface — finally camera rises upward and effect fades to black"

---

## Technical Implementation

### Source Files

| File | Purpose |
|---|---|
| `B.C` | Main demo loop for the voxel/sinus field part |
| `BA.ASM` | Assembly: core height-field renderer |
| `BDO.C` | "Do" routines — render iteration |
| `BDOOLD.C` | Earlier version of BDO |
| `BP.C` | Per-column projection code |
| `DOLINE.C` | Line drawing (for column rendering) |
| `EDGE.C` | Edge calculation |
| `GMAIN.C` | Standalone glenz test harness (not part of demo) |
| `KOE.C` | Test/experiment code |
| `VEC.ASM` | Vector routines (shared with GLENZ) |
| `VASM.INC` | ASM include for vector routines |
| `VDATA.ASM` | Vector data |
| `VMATH.ASM` | Vector math |
| `VMATHSIN.ASM` | Sine-based vector math |
| `VNEW.ASM` | Newer vector routines |

### Rendering Algorithm

The voxel landscape renderer works similarly to the Comanche engine:

1. **For each vertical screen column** (0..319):
   - Cast a ray from the camera at the appropriate horizontal angle
   - March along the ray in the XZ plane
   - At each step, sample the height field `h = f(x, z)`
   - Project the top of each height column onto the screen
   - Draw a vertical strip from the previous top to the new top

2. **Height field function:**
   - `h(x, z) = sin(x*freq1 + time) + sin(z*freq2 + time) + ...`
   - Multiple summed sine waves at different frequencies and phases
   - Animated by advancing `time` each frame

3. **Colour:** Each column height maps to a colour (depth shading + height shading)

### Height Map from Sine Field

The `SIN1024.INC` table provides fast integer sine lookups. The height at position (x, z) is computed as:

```c
// Pseudo-code approximation
h = sin1024[(x * fx + phase_x) & 1023] / scale
  + sin1024[(z * fz + phase_z) & 1023] / scale
  + sin1024[((x+z) * fxz + phase_xz) & 1023] / scale_2;
```

### LINEBLIT.INC

Shared with `GRID/`, this provides fast vertical column blitting — the core inner loop of the height-field renderer.

### Shared Glenz Renderer

`GMAIN.C` and the `VEC.ASM` / `VMATH.ASM` files in `HARD/` are the same glenz vector renderer used in `GLENZ/` — `HARD/` is actually a development testbed where both the glenz renderer and the height-field renderer were developed together.

The final `3DSINFLD.EXE` may only use the height-field portion.

### Assets

| File | Description |
|---|---|
| `FCKOE3.PAL` | Test palette |
| `FCLOGOS.LBM` | FC logos graphic |
| `PIC001.LBM` | Source picture |

---

## Surprising Details

- The `HARD/` directory name suggests this was the "hard" (difficult) part — the voxel renderer was technically very challenging for 1993 hardware
- `GMAIN.C` is a complete interactive glenz test harness with keyboard controls (keys 8/2/4/6 for rotation, +/- for Z depth, 't' for test mode, 'c' for close-up) — this was PSI's development environment
- The `lightshift` variable controlling glenz highlight brightness appears in both `HARD/GMAIN.C` and `GLENZ/MAIN.C` — the exact same variable name, confirming these share the same codebase
- `BDOOLD.C` contains the original version preserved alongside the improved `BDO.C`
- The voxel effect runs without texture mapping — only height-based flat shading — making it achievable in real-time on 486 hardware
