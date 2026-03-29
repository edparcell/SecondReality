# Part 11: Plasma + Plasma Cube (PLZPART)

**Directory:** `original/PLZPART/`
**Output EXE:** `PLZPART.EXE` (plasma and plasma cube combined)
**Coder:** Wildfire

---

## Visual Effect

**Plasma:** A full-screen animated plasma effect — smooth, flowing, multicoloured patterns that resemble liquid light or molten metal. The colours cycle through multiple palettes (red, blue, white, mixed) timed to the music. The plasma fills the entire 320×280-ish display area.

**Plasma Cube:** The plasma pattern is applied as a texture to a rotating 3D wireframe cube. The cube appears, grows, morphs, and eventually transitions out.

---

## Technical Implementation

### Source Files

| File | Purpose |
|---|---|
| `PLZ.C` | Main plasma render loop |
| `PLZFILL.C` | Plasma fill helper |
| `VECT.C` | Vector (cube) renderer |
| `MAIN.C` | Top-level: init, run plasma, run vectors |
| `PLZA.ASM` | Optimised assembly for plasma line rendering |
| `SPLINE.ASM` | Spline interpolation for smooth transitions |
| `MAIN.ASM` | Assembly main entry point |
| `COPPER.ASM` | Copper/VBlank palette management |
| `INCLUDE.ASM` | Shared includes |
| `TWEAK.ASM` / `TWEAK.H` | VGA mode tweaking |
| `ASMYT.ASM` | Assembly utilities |

### Plasma Algorithm

The plasma uses **summed-sine lookup tables** to generate smooth 2D patterns. The key tables:

```c
// psini[16384] — primary sine table
// lsini4[8192] — secondary sine table (4-cycle)
// lsini16[8192] — secondary sine table (16-cycle)
// ptau[256] — cosine-shaped fade table for palette transitions

// Each pixel (x,y) colour:
PLZSINI(p1,p2,p3,p4) =
    psini[x*32 + lsini[y*2+p2]*16 + p1] +
    psini[y*4  + lsini[x*64+p4]*4 + p3] +
    psini[x*32 + 16 + lsini[y*2+p2]*16 + p1] +
    psini[y*4  + lsini[x*64+32+p4]*4 + p3]) * 256;
```

The four parameters `p1..p4` are animated by the `l1..l4` and `k1..k4` variables which change each frame, creating the flowing motion.

The LINELEN × MAXY region (41×280 pixels per plane, displayed as 320 wide with bitplane tricks) is recomputed every frame.

### Tweaked Video Mode

The plasma runs in a tweaked VGA mode that appears to be **Mode X** or similar — 320 pixels wide but using the 4-plane VGA memory with specific CRTC settings to achieve a 280+ line display:

```c
cop_start = 96 * (682 - 400);   // CRTC split offset
set_plzstart(60);                // Y start for plasma rendering
```

The plasma renders alternating even/odd lines into different memory planes each frame via the Sequencer register:
```c
asm mov dx, 3c4h
asm mov ax, 0a02h    // plane 1 and 3 (0x0A = bits 1 and 3)
asm out dx, ax
// render even lines...
asm mov ax, 0502h    // plane 0 and 2 (0x05 = bits 0 and 2)
// render odd lines...
```

This doubling of plane writes creates a 4-colour lookup per pixel, enabling more colour combinations from the limited palette.

### Palette System

Six pre-built 256-colour palettes (`pals[6][768]`) transition between:
1. RGB cycling (red → black → blue → purple)
2. Red-black (high contrast red)
3. White (greyscale)
4. Red-blue-white
5. White II (dark to light)
6. (fifth state)

Palette transitions are triggered by a `timetable[]` keyed to music frame positions:
```c
int timetable[10] = {64*6*2-45, 64*6*4-45, 64*6*5-45, 64*6*6-45, 64*6*7+90, 0};
```

The copper routine handles smooth palette crossfades each VBlank via `cop_fadepal` pointer and `cop_drop` fade speed.

### SPLINE.ASM — Smooth Parameter Interpolation

The `l1..l4` and `k1..k4` values controlling the plasma pattern are linearly interpolated from `inittable[]` target values using spline interpolation, preventing jarring jumps when palette/pattern phases change.

### Plasma Cube (VECT.C)

After the flat plasma concludes, the plasma cube runs. This renders a 3D wireframe cube with the plasma colours applied:
- The cube rotates continuously
- The polygon faces use the same plasma colour indices as the flat plasma
- The cube is rendered using the standard polygon pipeline from the shared vector routines

### Assets

Data tables embedded in the EXE via `.INC` files:
| File | Description |
|---|---|
| `PSINI.INC` | Primary sine lookup table data |
| `LSINI4.INC` | Secondary sine table (4-cycle variant) |
| `LSINI16.INC` | Secondary sine table (16-cycle variant) |
| `PTAU.INC` | Cosine palette transition table |
| `SINIT.INC` | Sine initialisation data |
| `TILE.INC` / `TILEPAL.INC` | Tile palette data |
| `RATA.INC` | Rate/animation data |
| `PSINI.INC` | Plasma sine table |
| `SPLINE.INC` | Spline data |

---

## Surprising Details

- The `DO_TABLES` compile-time flag in `PLZ.C` regenerates all the `.INC` data files from scratch using floating-point math — in the final build, these are pre-baked
- The formula `lsini4[a] = (sin(a*DPII/4096)*55 + sin(a*DPII/4096*5)*8 + sin(a*DPII/4096*15)*2 + 64)*8` shows the multi-harmonic nature of the sine tables — multiple frequency components add to make the pattern more organic
- The first palette entry (index 0) is black in the initial palette — this was intentional so the first palette frame shows plasma appearing from blackness
- The initial palette `pals[0]` is set to all-white initially, then modified: `for(a=0;a<768;a++,pptr++) *pptr = (*pptr-63)*2` — this shifts the palette to make the initial appearance white-hot
