# Part: Twist Effect (TWIST)

**Directory:** `original/TWIST/`
**Status:** Development/unused — may have been cut from the final demo

---

## Visual Effect

A horizontal twist/wave distortion effect applied to the entire screen. Each row of pixels is shifted left or right by an amount that varies sinusoidally with Y position and time, creating a wobbly/twisting appearance. The shift amount per row is animated, making the twist appear to flow.

---

## Technical Implementation

### Source Files

| File | Purpose |
|---|---|
| `MAIN.C` | Main loop: calculates twist table, calls twister |
| `TWIST.ASM` | Core assembly: applies the twist distortion per row |
| `ASM.ASM` | Assembly entry points |
| `DOL.C` | Demo loop wrapper |
| `DOLOOP.C` | Loop control |
| `KOE.ASM` | Test code |
| `SIN1024.INC` | Sine table |
| `TWSTLOOP.INC` | Twist inner loop unroll |

### Algorithm

The twist works by per-row horizontal scroll using VGA double-buffering:

```c
// For each row y:
w = sin1024[((r >> 6) & 511) + 256] * 25/64 + 100;
twist[y*4 + 0] = w;   // horizontal offset for this row
r += ra;               // phase accumulates
ra++;                  // phase rate increases each frame
```

`ra` increases each frame, so the twist accelerates — the wave frequency increases over time.

### Double Buffering

The twist uses **dual-page VGA buffering** to eliminate flicker:
```c
vram1 = (char far *)0xa0000000L;  // page 0 at offset 0
vram2 = (char far *)0xa8000000L;  // page 1 at offset 0x8000

// Alternate between pages each frame:
outp(0x3d4, 0x0c);
outp(0x3d5, 0x80);  // display page 1 (offset 0x8000)
waitb();
vram = vram1;        // render into page 0

// next frame:
outp(0x3d4, 0x0c);
outp(0x3d5, 0x00);  // display page 0
waitb();
vram = vram2;        // render into page 1
```

### TWIST.ASM — Per-Row Blitter

The `twister()` routine applies the horizontal offset table. For each row:
1. Read the target offset from `twist[y*4]`
2. Source the row pixels from the offscreen buffer
3. Write them to the display buffer shifted by the offset amount

This creates the horizontal wave distortion.

### Assets

| File | Description |
|---|---|
| `TMP.LBM` | Temporary test image |

---

## Surprising Details

- The twist effect is not clearly identifiable in the final released demo — it may have been cut or absorbed into another part's transition
- The `DOLOOP.C` / `DOL.C` / `MAIN.C` split shows the typical Future Crew development pattern: test harness separated from the demo-ready loop
- The use of `vram2` at address `0xa8000000L` maps to VGA segment `0xA800` — this is a 32KB offset within the 64KB VGA window, used as a second page in 320×200×256 mode (which only needs 64000 bytes, leaving room for a second full page at offset 0x8000 = 32768 bytes, but also offset 0xFA00 for the full 64000... Actually VGA Mode 13h has 64KB of addressable memory and 64000 bytes used per page, so two pages fit just barely: page 0 at 0x0000, page 1 at 0xFA00. The 0x8000 offset here suggests a different memory layout or mode.)
- The sine-driven `w` calculation `sin1024[...+256]*25/64+100` centres the twist around column 100, with amplitude of ±25 pixels — a subtle but visible effect
