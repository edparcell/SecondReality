# Surprising and Notable Details

A collection of the most interesting, unexpected, or technically impressive findings from the source code.

---

## Original Finnish Design Documents

The root directory contains plaintext design documents written in Finnish:

- **`DESIGN`** — The original visual concept description. Written partly in Finnish, it describes each section's intended visual effect in poetic, aspirational terms. For example, the Music credits section was originally intended to feature "ylimassiivinen musa" (ultra-massive music), "infraääni ylitse muiden hajoittaa kaiuttimet" (infrasound to destroy speakers), and "koko demoscene saa yhden ison sydänkohtauksen ja kuolee pois" (the entire demoscene gets one big heart attack and dies).
- **`SCRIPT`** — A production status document. Lists each part's completion percentage and assigned developer, alongside Finnish scene descriptions. Notable: PSI's Comanche voxel renderer was listed at 99% done, his Lens+Rotozoomer at 99%, and his Glenz vectors at only 50% at the time this was written.
- **`IDEAS`** — Unused ideas: "new year bang", "rotating fire jets burning the earth", "shadebobs", "2D jello block", "dotcuberise"
- **`VECSCR`** — The vector part script (from `#include "vecscr"` in SCRIPT)

---

## The Demo Was Originally Called "Unreal 2"

All internal references use "U2" or "UNREAL 2":
- Source files: `U2.ASM`, `U2A.EXE`, `U2E.EXE`
- Variables: `u2_text SEGMENT`
- Comments: `; UNREAL 2 - Init/Deinit part`

Second Reality was the sequel to "Unreal" (1992), also by Future Crew.

---

## Hidden Copyright Message in Stack Space

In `U2.ASM`, the copyright notice is embedded in the 1KB stack area at the very start of the code segment:

```asm
ORG 0h
;---[between these two, there is the stack]---
db 13, 25 dup(10)
db '·S·E·C·O·N·D·  ·R·E·A·L·I·T·Y· (beta)   Copyright (C) 1993 The Future Crew ', 13, 10
db '$'
;---[between these two, there is the stack]---
ORG 400h  ; 1K stack
```

The copyright text literally lives inside the stack memory. This is a clever trick — the text is permanently in memory, can be found with a hex editor in the EXE, but the CPU ignores it (it's just overwritten as the stack grows down).

The word "(beta)" was apparently left in even in the final release.

---

## Windows Detection

```c
if (getenv("windir")) {
    *ip = -3;
    return;
}
```

The demo actively refuses to run under Windows. This was a real concern in 1993 (Windows 3.1 was current), and it's the first thing `START.EXE` checks. Error code -3 is then caught by the main loader which displays "Sorry, but this program cannot run under Microsoft Windows (tm)."

---

## Pre-Recorded Physics Paths

The lens effect (`LENS/MAIN.C`) and rotozoomer originally computed physics simulations in real-time (with `#define SAVEPATH`), then **recorded the results to files** (`lens.exp`). The final demo plays back these pre-recorded paths:

```c
#ifndef SAVEPATH
x = pathdata1[frame*2+0];  // replay pre-recorded x position
y = pathdata1[frame*2+1];  // replay pre-recorded y position
drawlens(x, y);
#endif
```

This guaranteed perfect music synchronisation regardless of CPU speed — the effect runs at the same "speed" visually even on slow 386 machines, because the positions are time-indexed, not physics-computed.

---

## "Paska" 3D Model

`original/3DS/PASKA2.3DS` — "paska" is Finnish for "shit." This is a rough throwaway test geometry model. The name was never cleaned up, and it was shipped in the source release.

---

## TRUG is Mikko Turunen

The camera animation file is named `MIKKO.VUE` — this is the real first name of TRUG (Mikko Turunen), the team member responsible for the mountain scroll, dot tunnel, mirror-ball scroll, and the Praxis explosion rendering.

---

## 11 City Scene Iterations

The `3DS/` directory contains 10 versioned city project files: `U2CITY2.PRJ` through `U2CITY11.PRJ`. This shows the extensive iteration on getting the 3D city background right for the vector part. No `U2CITY1.PRJ` exists — presumably lost or the original name.

---

## EGA "Moire" Via Multi-Frame Persistence

The Techno/JPLOGO interference effect doesn't actually compute a moire pattern — it exploits the fact that EGA has 4 independent memory planes, and by cycling which plane is written to each frame while simultaneously cycling the display start address, old frames persist for multiple display frames. The visual "interference" emerges naturally from multiple overlapping images of slightly different rotational angles.

---

## The Lens Uses 4 Colour Layers

The lens effect renders 4 separate colour-shifted layers of the same image. Each layer uses a slightly different displacement map, simulating **chromatic aberration** (the effect where glass prisms split white light into colours). This gives the lens a rich "glass" appearance without any actual chromatic aberration calculation — just palette tricks.

---

## Stack-Based Random Numbers in Protection

The `MAIN/PROT/PACK.C` protection system generates "random" padding bytes for the encrypted EXE by calling `exerand()`:

```c
int exerand(void) {
    int a = rand();
    if (a < 4096)  return 0;
    if (a < 8192)  return rand() & 0xf;
    if (a < 16384) return rand() & 0x7f;
    return rand();
}
```

Most random bytes are 0 or small values — this biases the padding toward small values that the decompressor handles efficiently, reducing the encrypted EXE size.

---

## The Assembly Syntax is Non-Standard

The source uses a mixture of:
- **MASM** syntax in main loader files (`U2.ASM`)
- **Inline assembly in Borland C** (`_asm { ... }` blocks)
- **PASCAL-style calling convention** in many ASM files (`PROC FAR`, parameters implicitly from stack in calling order)
- **Local labels** with `@@` prefix (MASM LOCALS directive)

The `.386` directive enables 32-bit registers (EAX, etc.) in 16-bit code — used for 32-bit arithmetic operations like `movsd` (move 4 bytes at once) in inner loops.

---

## Two Completely Separate Sound Card Paths

The music system has two completely different memory architectures:
- **SoundBlaster:** Music loaded to EMS (Expanded Memory Spec, a bank-switching scheme). Requires 1MB EMS and 50 EMS handles.
- **Gravis UltraSound:** Music loaded to the card's own 512KB RAM. No EMS needed. The GUS path is simpler and needs less CPU overhead.

The initial memory check `cmp bx, 80a0h` (≈32928 16-byte paragraphs = ~527K) is reduced from the stated 570KB — it checks for 527KB because the GUS path needs less conventional memory.

---

## Demo Loop Exploits the SCRIPT Comment in U2.ASM

The part list in `U2.ASM` has commented-out `db 'txt...'` strings that described each part for developers. These were deliberately removed from the assembly to save memory, but the comments remain. This is essentially inline documentation of the intended sequence:

```asm
;txt1  db 'Alkutekstit I (WILDF)       ',0    ; Opening credits I (Wildfire)
;txt2  db 'Alkutekstit II (PSI)        ',0    ; Opening credits II (PSI)
;txt3  db 'Alkutekstit III (TRUG/WILDF)',0    ; Opening credits III (TRUG/Wildfire)
;txt4  db 'Glenz (PSI)                 ',0    ; Glenz vectors (PSI)
;txt5  db 'Dottitunneli (TRUG)         ',0    ; Dot tunnel (TRUG)
;txt6  db 'Techno (PSI)                ',0    ; Techno (PSI)
;txt7  db 'Panicfake (WILDF)           ',0    ; Panic end (Wildfire)
```

"Alkutekstit" = Finnish for "opening text/credits"

---

## The `fill_object[]` Buffer Tracks Object IDs per Pixel

The 3D renderer (`VISU/C/MAIN.C`) maintains `fill_object[64000]` alongside `fill_color[64000]`. Every polygon fill writes the object's index into `fill_object` as well as the colour into `fill_color`. This enables:
- Picking (click on a pixel, know which object was hit)
- Per-object post-processing
- The Z-sort report during development: `print("[%s(%i): %li]", co[order[a]].name, ...)`

In the shipped demo, `fill_object` is mostly just overhead — but it reveals the tool was also a 3D scene previewer/editor, not just a renderer.

---

## The Protection is Layered on LZEXE

The demo's final EXE is:
1. First compressed with **LZEXE** (a well-known DOS EXE compressor)
2. Then encrypted/protected twice with **Future Protector IV** (their custom multi-layer XOR/ADD cipher)

The protector verifies the LZEXE signature (`LZ91`) in the input file before proceeding. Two protection passes are applied with different random keys each time. The encryption keys are derived from the EXE header fields (CS, IP, SS, SP) plus a random seed.

---

## Assembly "Copper" on PC

The copper-style interrupt system in `COPPER.ASM` / `DIS` fires callback routines at vertical blank intervals. On the PC, there is no hardware copper (unlike the Amiga), so this is implemented with timer interrupts. The callback routines change palette entries during VBlank to create scanline-level colour effects — but without hardware-level precision, they affect the entire frame rather than specific scanlines.

True per-scanline effects (like the `ALKU` widescreen letter-boxing) are achieved using the CRTC split-screen register, which is a genuine hardware feature.
