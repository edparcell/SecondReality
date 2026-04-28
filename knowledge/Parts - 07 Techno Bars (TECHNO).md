# Part 07: Techno Bars (TECHNO)

**Directory:** `original/TECHNO/`
**Output EXE:** `TECHNO.EXE`
**Coder:** PSI

---

## Visual Effect

The demo switches from MCGA 256-colour mode to **EGA 16-colour mode**. Multiple angled bars (parallelogram-shaped polygons) rotate around the centre of the screen in EGA planar memory. The bars accelerate until they become a blur, then a percussion hit freezes the screen with a flash, transitions briefly to a still image of a troll/character, and the demo returns to MCGA mode.

---

## Technical Implementation

### Source Files

| File | Purpose |
|---|---|
| `KOE.C` | Main demo loop, bar rendering, EGA mode management |
| `KOEA.ASM` | Assembly for EGA write routines |
| `KOEB.ASM` | More EGA routines |
| `POLYCLIP.ASM` | Polygon clipper for EGA drawing |
| `ROT.ASM` | Rotation / transform routines |
| `READP.C` | Packed picture reader |

### Video Mode

This part uses EGA **Mode 10h** (640×350×16 colours) with planar memory access. EGA has 4 memory planes (bit planes 0–3), each contributing 1 bit to the 4-bit colour index per pixel.

However, the actual mode used is likely a tweaked EGA mode closer to 320×200 with planar tricks, accessed as if it were 160 bytes wide (40 columns × 4 planes = 160 bytes per row for 320 pixels).

The `POLYCLIP.ASM` does clipped polygon rendering into EGA planar memory.

### EGA Planar Writing

To draw a solid bar in EGA:
1. Set the EGA Write Mode and the Bit Mask register to select which pixels to update
2. Write to the appropriate plane via the Sequencer register (port 0x3C4, register 2)
3. Use the EGA latch for XOR/OR operations to combine planes

The rotating bars use these plane-level operations to create the 16-colour palette effects.

### Bar Geometry (from JPLOGO/JP.C which reuses the techno style)

The bars are drawn as rotated rectangles. The `KOE.C` in TECHNO controls:
- Rotation angle per frame
- Number of bars / spacing
- Scale variation (bars grow/shrink as they rotate)

### Transition to Still Image

After the acceleration peak:
1. Screen flashes white
2. VGA mode switches back to MCGA 320×200
3. A packed image (likely `PANICPIC.LBM` — the troll/still) is loaded and displayed
4. EGA state is saved via DIS message area 1 for mode-switching back

### Assets

| File | Description |
|---|---|
| `PANICPIC.LBM` | Still image shown after the flash (the "Jellykuva" / troll picture per the SCRIPT) |

---

## Surprising Details

- The SCRIPT file describes this as: "techno bars rotate, etc. — finally speed increases until *BANG* — screen freezes (flashes at same time) — still for a moment — MCGA tweak — nice picture [320×400×256]"
- The EGA → MCGA transition is tricky because both modes use different memory layouts; DIS message areas 1 and 2 are specifically reserved for storing VGA/EGA state during transitions
- `POLYCLIP.ASM` in this directory is a general polygon clipper, used to keep bar polygons within screen bounds during extreme rotation angles
- The `PANIC/` directory contains `SHUTDOWN.C` which handles the "panic end" — a separate part where the screen shrinks to a dot. These are two different visual concepts despite sharing a name: "Techno" leads into the panic-style screen reduction
