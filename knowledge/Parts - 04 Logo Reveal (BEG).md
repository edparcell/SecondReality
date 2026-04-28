# Part 04: Logo Reveal — "Second Reality" Title (BEG / BEGLOGO)

**Directory:** `original/BEG/`
**Output EXE:** `BEGLOGO.EXE`
**Coder:** Wildfire / PSI
**Graphics:** Pixel

---

## Visual Effect

After the explosion flash, the "Second Reality" logo appears. It starts monochrome (from the flash) and the colours fade in. The logo then appears to "bounce" into position — it zooms in from a distance with jelly/bounce physics, settling into its final position with damped oscillation.

---

## Technical Implementation

### Source Files

| File | Purpose |
|---|---|
| `BEG.C` | Main loop: logo display, bounce physics, fade |
| `ASM.ASM` | Assembly helpers (mode setup, blitting) |
| `READP.C` | Reads packed picture format (`.UP` files) |
| `CLINK.INC` | Include for linker/segment config |
| `MAKEFILE` | Build script |

### Assets

| File | Description |
|---|---|
| `SRTITLE.LBM` | "Second Reality" title graphic (IFF ILBM) |
| `SRTITLE.UP` | Packed version of the title for runtime |
| `TMP.BBM` | Temporary bitmap work file |
| `_PIC.OBK` | Object binary — embedded picture data |

### Bounce Physics

The logo uses simple spring/damping physics to produce the bounce effect:
- `ypos` — current Y position (starts off-screen above)
- `yposa` — vertical velocity
- `boingm` / `boingd` — bounce multiplier/divisor (ratio controls energy loss per bounce)

Each bounce multiplies velocity by `-boingm/boingd`, with `boingm` and `boingd` updated each bounce to increase damping (the ratio tends to 1 as bounces continue, eventually settling).

### Fade-In Sequence

1. Screen starts white (from PAM explosion flash)
2. Logo is blitted in white-on-white (invisible)
3. Palette fades from white to greyscale, revealing the logo monochromatic
4. Palette then cross-fades from greyscale to full colour

---

## Surprising Details

- The `.UP` packed picture format is a custom run-length encoding used throughout Second Reality for picture data storage within EXEs
- The `READP.C` file (shared with multiple parts) handles decoding the `.UP` format
- The logo graphic was created at 320×400 resolution (double height) to allow crisp rendering in the tweaked VGA mode
