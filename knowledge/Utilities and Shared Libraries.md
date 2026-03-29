# Utilities and Shared Libraries

## Overview

Several utility systems are reused across multiple demo parts. Understanding these is essential for replicating the demo in Python/OpenGL.

---

## TWEAK — VGA Mode Tweaking (`TWEAK.ASM`, `TWEAK.H`)

Found in: `ALKU/`, `CREDITS/`, `PAM/`, `PLZPART/`, `START/`, etc.

### Purpose
Provides routines to set non-standard VGA modes by writing directly to CRTC, Sequencer, and Attribute registers. Key functions:

- `tw_opengraph()` — switch to tweaked 320×200 VGA mode (Mode X style)
- `tw_opengraph2()` — switch to tweaked mode variant 2 (wider/taller)
- `tw_closegraph()` — restore standard text mode
- `tw_setpalette(pal)` — upload 256-colour palette from 768-byte array
- `tw_setrgbpalette(index, r, g, b)` — set single palette entry
- `tw_putpixel(x, y, col)` — write pixel (handles planar memory)
- `tw_getpixel(x, y)` — read pixel
- `tw_setstart(offset)` — set CRTC display start address
- `tw_setsplit(y)` — set CRTC split-screen Y position
- `tw_clrscr()` — clear the display buffer

### VGA Register Access

All VGA programming is done via direct I/O port writes:
- `0x3C8` / `0x3C9` — DAC palette address / data
- `0x3C7` — DAC read address
- `0x3D4` / `0x3D5` — CRTC index / data
- `0x3DA` — VGA status register (bit 3 = vertical blank, bit 0 = horizontal blank)
- `0x3C4` / `0x3C5` — Sequencer index / data (plane masking)
- `0x3CE` / `0x3CF` — GDC index / data (read plane select)
- `0x3C0` / `0x3C1` — Attribute controller (pixel panning, split-screen)

---

## SIN1024 — Sine Lookup Table (`SIN1024.INC`)

Found in: almost every part directory.

A 1024-entry 16-bit integer sine table:
- `sin1024[0..1023]` maps `[0..1023]` → `[-1024..1024]` (approximately)
- Cosine: `sin1024[(a + 256) & 1023]`
- Full period = 1024 entries

Used for all trigonometric calculations throughout the demo (rotation, oscillation, parametric curves).

`SIN4096.INC` (in `LENS/`) provides a 4096-entry variant for higher-precision calculations.

---

## READP — Packed Picture Reader (`READP.C`)

Found in: `BEG/`, `END/`, `ENDPIC/`, `JPLOGO/`, `TECHNO/`

Reads the custom `.UP` (uncompressed packed) picture format used throughout the demo. `.UP` files contain:
- Palette data (packed RGB triplets)
- Pixel row data (run-length compressed scanlines)

The `readp(palette, row, pic)` function:
- `row = -1`: reads the palette
- `row = 0..N`: reads and decompresses row N into a buffer

---

## FCP — File Compression Pack (`original/FCP/`)

### Pack.C

Creates compressed archive files (`.FC`):
- Reads input EXE files
- Applies delta + RLE compression
- Outputs a packed archive with a file directory

### Unpack.ASM

The decompressor stub:
- Small assembly routine that decompresses data from the `.FC` archive
- Embedded as a binary blob in the main loader

### Print.C

Utility for printing compression statistics.

---

## GRAB — Development Asset Tools (`original/GRAB/`)

A collection of tools for processing and converting graphics assets:

| File | Purpose |
|---|---|
| `LOADLBM.C` | Loads IFF ILBM (.LBM) files |
| `LBM2P.C` | Converts LBM to packed `.P` format |
| `LBM2U.C` | Converts LBM to uncompressed `.U` format |
| `LBM16.C` | 16-colour LBM handling |
| `VIEWLBM.C` | LBM viewer utility |
| `PALVIEW.C` | Palette viewer |
| `GFX.C` | General graphics utilities |
| `VP.C` / `VPL.C` | Viewport / view-plane utilities |
| `SP.C` | Sprite packer |
| `AO.C` | Animated object tool |
| `COL.C` | Colour manipulation |
| `SFCP.C` / `LFCP.C` | Save/Load FCP archives |
| `DEFLBM.INC` | Default LBM include definitions |
| `WC2CONV.INC` | Watcom C2 conversion macros |
| `GFXSAVE.H` | Graphics save header |

### FLIC tools (`GRAB/FLIC/`)

Tools for working with Autodesk Animator FLI/FLC animation files:
- `SHOW.C` — play a FLI animation
- `VF.C` / `VFLI.C` / `VFOK.C` / `VW.C` / `VW2.C` — various FLI viewers/players

### Font tools (`GRAB/FONT/`)

Tools for processing the demo's custom bitmap fonts:
- `FONT1.C` — font handling v1
- `FONT2.C` — font handling v2
- `PRINT.C` — print text using font
- `TOBM.C` — convert to bitmap

### System Font (`GRAB/SYSFONT/`)

- `F.C` — system font tool
- `FONT8X14.INC` — standard 8×14 pixel system font data

---

## UTIL — Binary Object Utilities (`original/UTIL/`)

| File | Purpose |
|---|---|
| `DOOBJ.C` | Converts binary data to `.OBJ` format for linking into EXE |

This is used to embed data files (pictures, lookup tables, sound effects) directly into EXE files. The technique: run `DOOBJ` on a binary file, it produces a `.OBJ` with a single named segment containing the data, which can then be `LINK`ed into the EXE alongside C and ASM modules.

The segment can be given a paragraph-aligned starting offset so the data begins at offset 0 in its segment — important for far-pointer access in the 16-bit memory model.

---

## DIS — Demo Interrupt Server (`original/DIS/`)

See [[Architecture - Main Loader and DIS]] for full documentation.

| File | Purpose |
|---|---|
| `DIS.H` | Interface header (used by all parts) |
| `DIS.ASM` | Assembly implementation |
| `DISC.ASM` | Resident DIS for standalone testing |
| `DISDATE.INC` | DIS version date constants |
| `DISINT.ASM` | DIS interrupt vectors (included by main U2.ASM) |
| `DIS.H` | C header declaring all DIS functions |
| `DISTEST.C` | DIS test utility |

---

## COMAN — "Comanche" Common Utilities (`original/COMAN/`)

Despite the name (short for "Comanche" or "Common"), this directory contains:
- `MAIN.C` / `MAIN1.C` — test mains
- `DOLOOP.C` / `DOLOOP1.C` / `DOLOOP2.C` — loop wrappers
- `ASM.ASM` / `ASM1.ASM` — assembly helpers
- `THELOOP.ASM` / `THELOOP.INC` — the main render loop
- `KOE.C` — test code
- `WAVE.H` — wave/audio header
- `SIN1024.INC` — sine table
- `COMBG.LBM` / `COMBG.UH` — background image

This appears to be the development directory for the Comanche/voxel section, separate from `HARD/`. The two directories may represent different stages of development, with `HARD/` being the final version.

---

## START — Setup Utilities (`original/START/`)

| File | Purpose |
|---|---|
| `MAIN.C` | Main setup logic |
| `READP.C` | Packed picture reader |
| `ASM.ASM` | Assembly helpers |
| `CLINK.INC` | Linker configuration |
| `HZPIC.LBM` / `HZPIC.PAL` | Horizon/background picture for the setup screen |

The `START.EXE` setup module uses `HZPIC.LBM` as a background image for the opening credits section (different from `ALKU/` — this is the image seen when the setup screen transitions).

---

## MAIN — Main Loader Support (`original/MAIN/`)

| File | Purpose |
|---|---|
| `START.C` | Windows detection, reads menu results |
| `MENU.C` | Setup menu display and navigation |
| `VIDTEXT.C` | Text rendering for the VGA text-mode menu |
| `VGASAVE.C` | VGA state save/restore |
| `VMODE.ASM` | VGA mode detection and management |
| `COPPER.ASM` | Main loader copper routine |
| `U2.ASM` | Main loader (includes all above) |
| `U2A.ASM` | Assembly utilities for main loader |
| `LOADER.H` | Loader interface header |
| `STMIK.H` | STMIK music system header |
| `STMIKA.INC` | STMIK assembly code (included by U2.ASM) |
| `PACK.C` | FCP pack support (for distribution build) |
| `PACKFINA.INC` | Final pack file directory |
| `PACKING.INC` | Development pack directory |
| `TEST.C` | Loader test utility |
| `STARTEMS.C` | EMS (Expanded Memory) initialisation |
| `STARTMUS.C` | Music loader/initialiser |

### DATA/ subdirectory

Runtime data directory for the demo distribution — would contain all the part EXEs copied here from their respective build directories.

### DISTR/ subdirectory

Distribution-specific build outputs.

### PROT/ subdirectory — "Future Protector IV"

The protection system used on the released demo EXE:

| File | Purpose |
|---|---|
| `PACK.C` (or `PROT/CRYPT.C`) | EXE encryptor/packer |
| `ASMYT.ASM` | Assembly utilities |
| `RUN1.ASM` / `RUN2.ASM` / `RUN3.ASM` | Unpacker stubs |
| `RUN1.INC` / `RUN2.INC` | Stub includes |
| `EXEHEAD.INC` / `EXEBODY.INC` | EXE header templates |
| `SPLIT.C` | EXE splitter utility |
| `TEST.ASM` | Protection test |
| `TGIDT.ASM` | Target ID/detection code |

The protection encrypts the EXE contents with a multi-layer XOR/ADD cipher keyed from the EXE header values. The unpacker stub is appended to the encrypted body and sets the entry point so it runs first, decrypts, then jumps to the original entry point. Two passes of encryption are applied (see `FCP/PACK.C`).

---

## Music Files (`original/MAIN/`)

| File | Description |
|---|---|
| `MUSIC0.S3M` | First music module (intro/calm sections) |
| `MUSIC1.S3M` | Second music module (techno/energetic sections) |

S3M = ScreamTracker 3 Module format. These are the two music files for the entire demo, created by Purple Motion and Skaven. The demo restarts music from specific pattern positions (`bx` parameter in `restartmus`) at section boundaries.
