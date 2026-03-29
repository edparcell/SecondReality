# Development Workflow and Build System

## Overview

Second Reality was developed primarily with **Borland C** (16-bit, DOS) and **Microsoft MASM** (Macro Assembler), with Watcom C also referenced. The build system used simple `.BAT` batch files and project files (`.PRJ` — Borland IDE project format), not makefiles (though `BEG/MAKEFILE` exists as an exception).

---

## Compilers and Tools

| Tool | Use |
|---|---|
| Borland C (BC) | C compilation for demo parts |
| MASM / TASM | Assembly compilation |
| LINK / TLINK | Linker (Borland TLINK likely) |
| LZEXE | EXE compressor (applied before protection) |
| Future Protector IV | Custom EXE encryptor |
| LBM2P.EXE | Convert IFF LBM → packed `.P` format |
| LBM2U.EXE | Convert IFF LBM → uncompressed `.U` format |
| INCBIN.EXE | Embed binary files as assembly data |
| DOOBJ.C → DOOBJ.EXE | Convert binary files to linkable `.OBJ` |
| CUT64KB.EXE | Trim EXE to 64KB (segment size management) |
| Autodesk 3D Studio | 3D modelling (`.3DS` files) |
| Autodesk Animator | Animation and camera tracks (`.VUE`, `.FLI`) |
| DPaint (DeluxePaint) | Pixel art (`DP_PREFS` files present, `.BBM` brushes) |

---

## Directory Convention

From the `CODE` document:
- Each part has its own directory (e.g. `GLENZ/`, `LENS/`)
- All cross-part references use relative paths: `..\DIS\DIS.H`
- Data files embedded via INCBIN or DOOBJ into part EXEs
- Part EXEs copied to `MAIN/DATA/` for the combined demo build

---

## Typical Part Build Process

1. **Write C + ASM code** in part directory
2. **Convert assets:**
   - `LBM2P filename.lbm` → `filename.P` (packed)
   - `LBM2U filename.lbm` → `filename.U` (uncompressed)
   - `DOOBJ data.bin data.obj` → linkable object
3. **Compile:**
   - `bcc -ml -3 main.c asm.obj data.obj ...` (large memory model, 386 instructions)
   - `masm asm.asm,asm.obj`
4. **Link:**
   - `tlink /x @response.rsp`
5. **Test with DIS resident:**
   - Install DIS TSR
   - Run part EXE from command line
   - `dis_indemo()` returns 0 in this mode (standalone)
6. **Copy to MAIN/DATA/**
7. **Build combined demo (MAIN/ makefile)**

---

## Memory Model

All C code uses **large memory model** (`-ml` compiler flag):
- Far pointers by default (segment:offset)
- Code and data can each be >64KB
- `char far *vram = (char far *)0xa0000000L` — explicit far pointer to video memory

The `halloc()` / `hfree()` functions allocate **huge** memory blocks spanning multiple segments.

Assembly code uses `.MODEL large, PASCAL`:
- FAR calls between segments
- PASCAL calling convention: parameters pushed left-to-right, callee cleans stack

---

## The DIS Resident Test System

The `DIS/DISC.ASM` file is a **TSR (Terminate and Stay Resident)** version of DIS for testing parts standalone:
1. Run `DISC.EXE` to install DIS as a resident interrupt handler
2. Run any demo part EXE directly from DOS
3. `dis_partstart()` finds the resident DIS via interrupt
4. All sync/music functions work (with music obviously not playing)
5. `dis_exit()` triggers on any keypress

This allowed each part to be developed and tested independently before integration into the main demo.

---

## The Pack File System

For the final release:
1. All part EXEs are compressed with LZEXE
2. Protected with Future Protector IV (two passes)
3. Packed into `REALITY.FC` using the FCP tool
4. The `PACKING.INC` file contains the pack directory (offsets + sizes)
5. `U2.EXE` reads `REALITY.FC`, finds the requested part, decompresses it, executes it

The `MAIN/DATA/` directory would contain the distributed files:
- `SECOND.EXE` (= `U2.EXE` renamed)
- `REALITY.FC` (pack file containing all parts)
- `MUSIC0.S3M`, `MUSIC1.S3M`
- `README.1ST`, `FCINFO10.TXT`

---

## Version History Hints

Several files show iterative development:

- `DOLOOP.C` / `DOLOOP1.C` / `DOLOOP2.C` — three versions of loop wrapper
- `MAIN.C` / `MAIN1.C` — two versions of main
- `NEW.ASM` / `NEW1.ASM` / `NEW2.ASM` — three revisions of routines
- `MAINNORM.C` / `MAINTRAN.C` — separate variants for different modes
- `U2AOLD.C` / `U2EOLD.C` / `BDOOLD.C` — old versions preserved alongside new

The pattern of keeping `OLD` versions alongside current ones suggests the team worked without a formal version control system (CVS etc. were available but uncommon in the demo scene).

---

## Cross-Part Include Pattern

Shared code is included via relative paths, not a library:
```c
#include "..\dis\dis.h"      // DIS header
#include "tweak.h"           // VGA tweak header
#include "vgasave.c"         // VGA save (included as .C, not compiled separately)
#include "vidtext.c"         // Video text (same)
#include "readp.c"           // Picture reader (same)
```

Including `.C` files directly (not just headers) was a common DOS-era technique to avoid complex makefiles and linker scripts. The "library" file is compiled once as part of whichever translation unit includes it.

---

## Memory Layout (Runtime)

```
0x0000:0x0000  DOS interrupt vector table (saved/restored by U2.EXE)
0x0000:0x0400  BIOS data area
...
[conventional memory]
   COMMAND.COM (if in memory)
   [TSRs if any]
   U2.EXE (the loader + DIS + STMIK)
   [free memory]
   [loaded part EXE - swaps in/out]
[EMS memory - for music on SoundBlaster]
   MUSIC0.S3M or MUSIC1.S3M
0xA000:0x0000  VGA memory (framebuffer)
0xB800:0x0000  Text video memory (used during menu)
```

The loaded part EXE is placed in the free conventional memory by DOS's EXEC function. When the part finishes, its memory is freed and the next part is loaded in its place.

Minimum memory requirement: 570,000 bytes free (GUS/no-sound) or more with SoundBlaster (EMS needed for music).
