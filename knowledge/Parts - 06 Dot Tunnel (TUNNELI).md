# Part 06: Dot Tunnel (TUNNELI)

**Directory:** `original/TUNNELI/`
**Output EXE:** `TUNNELI.EXE` (combined with GLENZ exit transition)
**Coder:** TRUG

---

## Visual Effect

512 bright dots emerge from the central glenz object and swirl outward in a tunnel/vortex pattern, creating the impression of flying through a tunnel made of light particles. The dots move in circular paths at varying depths, with depth-based brightness shading (closer = brighter). The tunnel fades out as the part transitions to the techno section.

---

## Technical Implementation

### Source Files

| File | Purpose |
|---|---|
| `ROUTINES.ASM` | Core dot rendering assembly routine |
| *(no C source present)* | Main C logic is likely embedded in the combined EXE |

### ROUTINES.ASM — Dot Renderer

The assembly routine `Putrouts` (PASCAL calling convention, FAR model) handles:

**Parameters:**
- `ax` — position data segment
- `si` — position data offset (array of x,y pairs)
- `dx` — background segment (for background pixel restore)
- `cx` — (unused in this variant — was font segment in FOREST version)
- `bx` — font/colour offset

**Algorithm per dot:**
1. Read old position from `oldpos[bx]` array
2. Clear old position: `es:[di] = 0`
3. Read new x from `ds:[si]`, new y from `ds:[si+2]`
4. Add `bx` (y-base) to y value
5. Clip to screen bounds (0..319 x, 0..199 y)
6. Compute screen offset: `di = x + rows[y*2]`
7. Write dot colour (15 = white) to `es:[di]`
8. Save new position to `oldpos[bx]`

The routine processes 64 dots per call (loop count in `cx=64`).

**`oldpos[]`** — a 7000-entry word array storing previous screen positions for erase-before-redraw.

**`rows[]`** — precomputed row start addresses: `rows[y] = y * 320`.

### Dot Physics (C side, in DOTS/)

The `original/DOTS/MAIN.C` file contains the full dot system (note: `DOTS/` is likely the combined `TUNNELI.EXE` source):

**Dot structure:**
```c
struct {
    int x, y, z;        // 3D position
    int old1..old4;     // previous screen positions (for motion blur / trail)
    int yadd;           // vertical velocity
} dot[512];
```

**Animation phases** (512 dots, `frame` counter):

| Phase | Frames | Behaviour |
|---|---|---|
| 0 | 0–500 | Dots form a sine-wave sphere shape (appearing from the glenz) |
| 1 | 500–900 | Dots move to a ring, then upward with `yadd=-260` |
| 2 | 900–1700 | Dots form a tunnel: radius = sin1024[frame&1023]/8, yadd=-300 |
| 3 | 1700–2360 | Dots scatter randomly across the screen |
| 4 | 2360–2400 | Palette fades brighter (flash) |
| 5 | 2400–2440 | Palette fades to black |

**Position formulas (tunnel phase):**
```c
a = sin1024[frame & 1023] / 8;  // tunnel radius varies sinusoidally
dot[i].x = icos(f*66) * a;       // x: cosine of dot's angular position
dot[i].z = isin(f*66) * a;       // z: sine of dot's angular position
dot[i].yadd = -300;               // all dots drift upward
```

This gives a swirling tunnel appearance as dots at different y-depths spiral upward.

### Rotation and Depth Projection

The main loop applies a rotation (`rot`) to all dots before projection. The rotation angle wobbles with `rots` oscillating with `rota`:
```c
if(frame > 1900) {
    rot += rota/64;
    rota--;            // rotation decelerates as frame increases
} else rot = isin(rots);  // rotation follows a sine wave early on
```

Depth cues:
- `depthtable1..4[]` — 128-entry lookup tables that map Z-depth to a colour index
- Closer dots (smaller Z) map to brighter colour palette entries
- The depth tables blend between the teal (`4,25,30`) and near-white (`16,55,60`) colours

### Background

The background for the tunnel is a gradient-filled screen: rows 100–199 are filled with a brightness ramp (`memset(vram+(100+a)*320, a+64, 320)` for a=0..99), creating a blue-to-black gradient behind the dots.

### Palette

```c
int cols[] = {
    0, 0, 0,       // black
    4, 25, 30,     // dark teal
    8, 40, 45,     // medium teal
    16, 55, 60     // bright cyan-white
};
// 16 entries per brightness level × 4 levels × per-dot-brightness
// = 64 palette entries for dot colours
```

---

## Surprising Details

- The `DOTS/` directory appears to be the actual source for `TUNNELI.EXE` — the directory name `TUNNELI` only contains `ROUTINES.ASM`, while `DOTS/` has the full C code and all supporting files
- The `dottaul[]` shuffle array is pre-shuffled with 500 random swaps, so dots appear/change in pseudo-random order rather than sequential order — this prevents obvious patterns when dots are re-assigned to new positions
- The `dis_musplus()` sync check `(a>-4 && a<0) break` exits the tunnel at a specific music cue, not just a timer
- The `bgpic` buffer (64KB) saves a copy of the initial background gradient so it can be used as the erase-and-redraw background
