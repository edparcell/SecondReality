# Part 15: Jelly Picture / Interference (JPLOGO)

**Directory:** `original/JPLOGO/`
**Output EXE:** `JPLOGO.EXE`
**Coder:** PSI
**Graphics:** Pixel / Marvel

---

## Visual Effect

This part runs in two phases:

**Phase 1 — Interference pattern:** An EGA-mode interference pattern of overlapping rotating wireframe boxes (similar to a Lissajous figure but 3D). The boxes rotate and create a moire-like pattern using EGA bitplane blending.

**Phase 2 — Jelly picture reveal:** A high-quality 320×400 pixel picture (troll/still image) "zooms in" from the centre in a wobbly jelly style, sliding in from the side via CRTC panning before settling into place with a ripple effect.

---

## Technical Implementation

### Source Files

| File | Purpose |
|---|---|
| `JP.C` | Main: EGA interference boxes + jelly picture transition |
| `JP3.C` | Alternative/earlier version |
| `DOL.C` | "Do loop" — frame iteration wrapper |
| `READP.C` | Packed picture reader |
| `ASM.ASM` | Assembly: EGA write routines, box draw |
| `SIN1024.INC` | Sine lookup table |
| `ZOOM.INC` | Zoom effect data |

### Phase 1: EGA Interference Boxes

The `doit1()`, `doit2()`, `doit3()` functions render rotating parallelogram boxes in EGA mode using multiple bitplanes:

**Core technique:**
- Video memory is 8000 bytes wide (320/4 × 80... wait, actually 40 bytes × 200 lines = 8000 bytes per plane in standard EGA)
- But here: `memset(vbuf, 0, 8000)` — 8KB buffer, so likely using a non-standard resolution or memory layout
- `asmdoit(vbuf, vram)` blits the buffer to EGA planes

**Box drawing (`asmbox`):**
- Computes 4 corners of a rotated rectangle using sine/cosine:
  ```c
  hx = sin1024[(rot+0)  & 1023] * 16 * 6/5;
  hy = sin1024[(rot+256)& 1023] * 16;
  vx = sin1024[(rot+256)& 1023] * 6/5;
  vy = sin1024[(rot+512)& 1023];
  // corners: (±hx ± vx, ±hy ± vy)
  ```
- 11 boxes drawn at different offsets along the minor axis

**EGA Plane Selection:**
```c
_asm mov dx, 3c4h
_asm mov ah, pl      // plane mask (1,2,4,8 cycling)
_asm mov al, 2
_asm out dx, ax
```

Each frame, a different EGA plane is written to. Combined with the start-address manipulation:
```c
a = plv * 0x20;
outp(0x3d4, 0x0c); outp(0x3d5, a);  // set display start address
plv++; plv &= 7;
```

This creates a 8-frame visual persistence effect — each frame's drawing persists for multiple frames due to the rotating plane/start-address combination, creating the moire/interference appearance.

**The 3 doit phases:**
- `doit1`: boxes at fixed size, rotation speed constant, `vm = 50`
- `doit2`: boxes with sinusoidal size variation, rotation accelerates
- `doit3`: boxes with CRTC-based horizontal panning (scroll), eventually the picture appears

### Phase 2: Picture Reveal (in doit3)

After the interference boxes, `doit3` loads the "troll" image (`troll.up`) and reveals it with:

**CRTC Horizontal Panning:**
```c
xpos = 320;  // start off-screen
xposa = 0;   // scroll velocity

// Each frame:
xpos += xposa/4;    // accelerate into view
xposa++;
// Set CRTC: outp(0x3d4, 0x0d); outp(0x3d5, xpos/4);
// Fine scroll: outp(0x3c0, 0x13); outp(0x3c0, (xpos&3)*2);
```

The picture slides in from the right at increasing speed, then decelerates and stops.

**Ripple effect:**
After the picture is fully in view, a ripple effect is applied using CRTC panning:
```c
xpos = 320 + sin1024[ripple & 1023] / ripplep;
ripple += ripplep + 100;
// ripplep grows each frame: ripplep *= 5/4
```

This makes the image wobble left-right with decreasing amplitude (like a jelly settling).

**Palette flash transition:**
When leaving phase 1:
```c
for(b = 0; b < 4 && !dis_exit(); b++) {
    // flash each EGA column white then black
    // creates stripe-flash transition
}
```

### Assets

| File | Description |
|---|---|
| `ICEKNGDM.LBM` | "Ice Kingdom" — the main still picture (Marvel or Pixel artwork) |
| `PIC.LBM` | Another picture asset |
| `TMP.BBM` | Temporary bitmap |

---

## Surprising Details

- The `power0[]` and `power1[]` arrays (16×256 bytes each) are look-up tables for amplitude-scaled values used in the interference rendering — they map `(amplitude_index, input_value)` to a scaled output
- `waitborder()` (not `dis_waitb()`) is used — it additionally handles palette flashing via `curpal`: when `dis_musrow() & 7 == 7`, `curpal` is set to 15, triggering a palette flash on beat
- The `asmdoit2` in `doit3` differs from `asmdoit` — it writes to a wider (non-square) memory layout matching the tweaked MCGA mode, not standard EGA
- The EGA interference effect uses a creative multi-frame persistence trick that gives 8 overlapping frames of boxes, creating complex moire patterns without any explicit interference calculation
- The comment `"GENERAL WINDOWS VIOLATION - REMOVE WINDOWS."` is a humorous error message for when memory allocation fails
