# Hidden Part: Desert Dream Stars (DDSTARS)

**Directory:** `original/DDSTARS/`
**Output EXE:** `DDSTARS.EXE`
**Coder:** PSI
**Visible:** Only when `whattorun` bit 7 is set (run with `SECOND U` command-line argument)

---

## Visual Effect

A starfield effect paying tribute to the demo "Desert Dream" by Kefrens (Amiga, 1993). Stars appear on screen and animate in a characteristic pattern. This is a hidden Easter egg part — it never appears in a normal playthrough of Second Reality.

---

## Technical Implementation

### Source Files

| File | Purpose |
|---|---|
| `DOIT1.C` | First EGA box generation tool (development utility) |
| `DOIT2.C` | Second EGA pattern tool |
| `DOIT3.C` | Third variant |
| `KR.C` | LFSR-based pixel pattern (test utility) |
| `KOE.ASM` | Assembly test |
| `STARS.ASM` | Star particle renderer |
| `POLYEGA.ASM` | EGA polygon renderer |
| `SIN1024.INC` | Sine table |
| `FLIP.INC` | Bit-flip lookup table |

### KR.C — LFSR Pixel Filler (Development Test)

`KR.C` is a simple test that fills VRAM using a linear feedback shift register (LFSR) pseudo-random sequence:
```c
_asm {
    mov ax, seed
    shl ax, 1
    jnc l1
    add ax, 0f7ffh    // XOR with polynomial if high bit was set
l1: mov seed, ax
}
vram[seed]++;
```

This visits all 64K video memory addresses in a pseudo-random order, creating a static noise pattern. Pure development test code.

### DOIT1.C — EGA Box Generator Tool

`DOIT1.C` generates an EGA-mode background pattern of concentric power-function rings:
```c
l1 = (double)(x - 320);
l2 = (double)(y - 200);
r = (int)pow(l1*l1 + l2*l2, 0.7);  // r^1.4 gives superellipse-like rings
a = (r/16) & 7;
vram[x + y*320] = a;
```

Then saves it as a planar EGA `.EGA` file. This appears to be a tool used to create the background artwork for the starfield effect.

### STARS.ASM

The actual star animation is in `STARS.ASM` — a particle system rendering stars as points or small shapes that animate in the Desert Dream tribute style.

### TEST/KOE.C

A subdirectory `DDSTARS/TEST/` contains `KOE.C` — another simple test (probably the most basic test, just writing a pattern to VRAM).

---

## Surprising Details

- The `DOIT1/2/3.C` files in `DDSTARS/` are completely different from the `TECHNO/KOE.C` files — they are standalone bitmap generation tools, not demo parts
- The `.EGA` file format (saved by `DOIT1.C`) is a planar 4-bit EGA format: for each row, 4 bitplane bytes are interleaved
- `KR.C` uses an LFSR with the polynomial `0xF7FF` — this generates a maximal-length sequence visiting all 65535 non-zero values before repeating
- The `FLIP.INC` lookup table bit-reverses bytes (maps bit 7→0, 6→1, etc.) — useful for EGA bitplane conversion where pixel order is MSB-first within each byte
- Running the demo with `SECOND U` triggers the hidden part (U = "hidden" in the part list comment in `U2.ASM`)
- The tribute to Desert Dream (an Amiga demo) in a PC demo was a notable cross-platform acknowledgment unusual for the time
