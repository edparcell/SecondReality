# Part 01: Opening Credits I — ALKU

**Directory:** `original/ALKU/`
**Output EXE:** `ALKU.EXE`
**Coder:** Wildfire
**Graphics:** Marvel (horizon bitmap), Pixel (font)

---

## Visual Effect

The opening credits sequence displays movie-style text on a black background, then fades into a wide-screen horizon panorama image that slowly scrolls left while further credit text fades in over it.

Text shown (synced to music):
1. "A" → "FUTURE CREW" → "production" (on black)
2. "First presented at Assembly '93" (on black)
3. Fade into wide horizon image
4. "Graphics by ..." scrolling over the moving image
5. "Music by ..."
6. "Code by ..." (with implied SFX: spaceship approaching from behind)

---

## Technical Implementation

### Source Files

| File | Purpose |
|---|---|
| `MAIN.C` | Main loop: font rendering, fade sequencer, scroll control |
| `ASMYT.ASM` | Optimised assembly routines for tweak mode |
| `COPPER.ASM` | Per-scanline palette cycling (copper effect) |
| `TWEAK.ASM` / `TWEAK.H` | CRTC register tweak for custom VGA mode |
| `INCLUDE.ASM` | Shared assembly includes |
| `FONA.INC` | Embedded font data (binary include) |

### Video Mode

The part uses a **tweaked MCGA mode** (320×400 pixels, 256 colours) achieved by writing directly to the CRTC registers. This doubles the vertical resolution by halving the line height. The horizon bitmap is 640×150 pixels, stored in the `.LBM` format.

### Scrolling Technique

The horizon image (width > 320) is scrolled by manipulating the CRTC start address register (registers 0Ch/0Dh), creating smooth sub-pixel horizontal scrolling without redrawing. The image is wider than the screen, so the start address is incremented each frame to create leftward movement.

### Font Rendering

The font (`FONA.LBM`, `FONA2.LBM`) is a custom bitmap font. Characters are looked up from a font table and blitted to the display buffer. The font supports 3-colour shading (light, medium, dark) for a subtle antialiased appearance on the 256-colour palette.

### Fade System

Multiple fade buffers are maintained:
- `fade1` — black palette
- `fade2` — text-only palette
- `picin[]` / `textout[]` — delta arrays for smooth linear palette interpolation each frame

The copper routine handles palette uploads during vertical blank to prevent tearing.

### Assets

| File | Description |
|---|---|
| `FONA.LBM` | Font bitmap (IFF ILBM format) |
| `FONA2.LBM` | Secondary font bitmap |
| `HOI.LBM` | Horizon panorama image |
| `HOIKKA.LBM` | Alternative horizon variant |
| `PIC001.LBM` | Fullscreen image |
| `RYPPIS.LBM` | Additional graphics |
| `U2-MOVIE.LBM` | "Movie style" background graphic |
| `HOI.IN0` / `HOI.IN1` | Packed/processed horizon data |

---

## Surprising Details

- The `ALKU.DSK` file is a floppy disk image — the entire intro was distributed on a single 1.44MB floppy
- The `LBM2U.EXE` and `LBM2P.EXE` tools in the directory convert IFF ILBM files to the custom `.U` (uncompressed) and `.P` (packed) internal formats used by the loader
- The `CUT64KB.EXE` tool was used to trim the packed EXE to under 64KB for segment boundary reasons
- The main C file (`MAIN.C`) uses `dis_sync()` values 1–8 to synchronise specific text appearances to exact music positions
