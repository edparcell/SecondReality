# Part 09: Mountain / Forest Scroll (FOREST / MNTSCRL)

**Directory:** `original/FOREST/`
**Output EXE:** `MNTSCRL.EXE`
**Coder:** TRUG

---

## Visual Effect

After the silence, trees and a mountain silhouette appear on screen. A scrolling logo/text banner scrolls across horizontally over the forest scene. The scene then fades to blue. This is a gentle, atmospheric transition section before the more intense effects that follow.

---

## Technical Implementation

### Source Files

| File | Purpose |
|---|---|
| `ROUTINES.ASM` | Core rendering assembly: composites font/logo over background |

### ROUTINES.ASM — Sprite Compositing

The `Putrouts` (FAR, PASCAL) routine composites a scrolling bitmap (font/logo) over a static background:

**Parameters:**
- `ax` — position/scroll data segment
- `si` — scroll data offset (run-length encoded sprite positions)
- `dx` — background image segment
- `cx` — font/sprite segment
- `bx` — current font column offset

**Algorithm:**
1. Loop 237×31 = 7347 iterations (31 rows × 237 columns of sprite)
2. For each position entry:
   - `lodsw` — read count of pixels to process
   - If count = 0: skip (transparent pixel row)
   - Otherwise: for each pixel, read destination address from `ds:[si]`
   - Read font pixel from `fs:[bx]`
   - If font pixel is non-zero: write it directly (opaque logo pixel)
   - If font pixel is zero: read background pixel from `gs:[di]` and write it (show background through transparent logo area)
3. Increment `bx` (advance font column)

This is a **sprite-over-background compositing** routine that correctly handles transparency — logo pixels that are zero show the background bitmap underneath.

### The `Putrouts1` Variant

A second variant (in `WATER/ROUTINES.ASM` and also `FOREST/`) with identical logic is used by the water/mirror scroll section. The scroll data format appears to be the same.

### Scroll Mechanism

The scroll position data is pre-built as a run-length encoded list of (destination_address, count) pairs for each row of the scrolling sprite. By incrementing the font column offset (`bx`) each frame, the sprite appears to scroll horizontally across the screen.

### Assets

| File | Description |
|---|---|
| `BACK1.LBM` | Forest/mountain background bitmap (static) |
| `FINAL.LBM` | Final state background |
| `FINAL2.LBM` | Alternative final background |
| `FONA.LBM` | Font/logo for the scroll text |
| `FONA2.LBM` | Secondary font variant |
| `HILLBACK.LBM` | Hill silhouette background layer |
| `KOE.LBM` | Test/development picture |
| `LOGO.LBM` | Logo graphic for the scroll |

---

## Surprising Details

- The SCRIPT says: "trees appear — scroll fades in — scroll scrolls by — [scroll is an image 320×31 that is some logo] — mountain fades to blue"
- The scroll format used here (run-length encoded pixel positions) is the same format used in the WATER/TUNNELI sections — a shared approach to sprite rendering
- The "fade to blue" at the end is the palette transition to the lens/rotozoomer section's colour scheme
