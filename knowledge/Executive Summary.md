# Second Reality — Executive Summary

**Release:** August 1993, Assembly '93 demoparty, Finland
**Group:** The Future Crew
**Platform:** IBM PC, MS-DOS, VGA/MCGA, 386+ CPU
**Category:** Demo (won 1st place at Assembly '93)

---

## What It Is

Second Reality is widely regarded as the greatest PC demo ever made. It is a non-interactive audiovisual program (a "demo") that runs entirely without data files beyond its single executable, showcasing realtime 3D graphics, plasma effects, lens distortions, tunnel effects, and a full original S3M soundtrack — all on DOS hardware from 1993.

It was created by a small Finnish group called **The Future Crew**, whose members included:

| Handle | Role |
|---|---|
| Purple Motion | Music |
| Skaven | Music |
| Marvel | Graphics |
| Pixel | Graphics |
| PSI | Code |
| Wildfire | Code |
| TRUG | Code, Rendering |
| Abyss | Design |
| Gore | Design |

---

## Architecture Overview

Second Reality is structured as a **loader/sequencer** (`U2.EXE`) that chains together a series of independent executable "parts". Each part is a separate DOS EXE file containing its own effect code and embedded data assets, loaded into memory, executed, and then freed before the next part runs.

```
U2.EXE  (Main loader + STMIK music player)
  ├── STARTMUS.EXE  — Initialises sound card & loads music to EMS
  ├── START.EXE     — Setup menu (sound card, quality, looping)
  ├── DDSTARS.EXE   — Hidden bonus part (Desert Dream Stars tribute)
  ├── ALKU.EXE      — Opening credits I: movie-style text (Wildfire)
  ├── U2A.EXE       — Opening credits II: giant 3D spaceship flyby (PSI)
  ├── PAM.EXE       — Opening credits III: Praxis explosion FLI animation (TRUG)
  ├── BEGLOGO.EXE   — "Second Reality" logo reveal with bounce (Wildfire/PSI)
  ├── GLENZ.EXE     — Glenz vectors (bouncing semi-transparent polyhedra) (PSI)
  ├── TUNNELI.EXE   — Dot tunnel (TRUG)
  ├── TECHNO.EXE    — Techno interference / rotating bars (PSI)
  ├── PANICEND.EXE  — Panic-style shrinking screen to dot (Wildfire)
  ├── MNTSCRL.EXE   — Mountain / forest scroll (TRUG)
  ├── LNS&ZOOM.EXE  — Lens effect + rotozoomer (PSI)
  ├── PLZPART.EXE   — Plasma + plasma cube (Wildfire)
  ├── MINVBALL.EXE  — Mini vector balls (PSI)
  ├── RAYSCRL.EXE   — Raytraced mirror-ball scroll (TRUG)
  ├── 3DSINFLD.EXE  — 3D sinus field / Comanche-style voxel landscape (PSI)
  ├── JPLOGO.EXE    — Jelly picture / interference picture (PSI)
  ├── U2E.EXE       — Vector part II: space battle (all)
  ├── ENDLOGO.EXE   — End picture / FC logo flash (Wildfire/PSI)
  ├── CRED.EXE      — Credits/greetings screen with scrolling photos (all)
  └── ENDSCRL.EXE   — End scroller (optional, disabled if looping)
```

---

## Key Technical Systems

### DIS — Demo Interrupt Server
A small resident interrupt server (`DIS`, in `original/DIS/`) that provides:
- `dis_waitb()` — wait for vertical blank, returns frames elapsed
- `dis_exit()` — check if user pressed a key
- `dis_musplus()` / `dis_musrow()` — music sync codes
- `dis_setcopper()` — register VBlank/HBlank callback routines
- `dis_msgarea()` — inter-part shared memory (64 bytes × 4 slots)
- `dis_indemo()` — detect if running inside demo vs standalone

DIS is installed by `U2.EXE` before any part runs. Each part calls `dis_partstart()` at the start.

### STMIK — Sound/Music System
STMIK (STuart's Music & Instrument Kit, embedded in `U2.EXE`) handles:
- S3M (ScreamTracker 3 Module) playback
- SoundBlaster mono/stereo (EMS required for music)
- Gravis UltraSound (512K card memory required)
- No-sound fallback mode
- Music loaded to EMS via `STARTMUS.EXE`

Music files: `original/MAIN/MUSIC0.S3M`, `MUSIC1.S3M`

### FCP — File Compression/Packing
The `original/FCP/` directory contains a compression tool that packs the executable files into `REALITY.FC`. The `original/MAIN/PACKING.INC` / `PACKFINA.INC` contain the packed file directory. The main loader decompresses parts on-the-fly.

### Tweak Mode (`TWEAK.ASM`)
Several parts use a custom "tweaked" VGA mode via direct CRTC register writes, enabling non-standard resolutions (e.g. 320×400, 360×480, etc.). The routines in `TWEAK.ASM`/`TWEAK.H` are shared across many parts.

### Protection (`MAIN/PROT/`)
The release EXE was protected with "Future Protector IV" — a multi-pass encryption scheme layered on top of LZEXE compression. Each layer uses XOR/add-based encryption with a rolling key derived from the EXE header checksums. This was to prevent casual copying/modification of the released demo.

---

## Demo Flow / Sequence

1. **Setup** — VGA text-mode menu: select sound card, quality, looping
2. **Opening credits I** — Movie-style fade-in text on widescreen horizon bitmap, scrolling left
3. **Opening credits II** — Massive 3D spaceship flyby (vector)
4. **Opening credits III** — Praxis-style ring explosion (FLI animation)
5. **Logo reveal** — "Second Reality" title bounces in with jellyball physics
6. **Glenz vectors** — Transparent/reflective polyhedra with light shading bounce and morph
7. **Dot tunnel** — 512 dots forming a swirling tunnel shape
8. **Techno** — Rotating wireframe bars in EGA 16-colour mode
9. **Panic end** — Screen shrinks to a point (Panic-demo homage)
10. **Mountain scroll** — Scrolling forest/mountain horizon with logo
11. **Lens + Rotozoomer** — Bouncing lens distortion, then rotating+zooming texture
12. **Plasma** — Summed-sine plasma in tweaked VGA mode
13. **Plasma cube** — Plasma mapped onto rotating 3D cube wireframe
14. **Mini vector balls** — Dot-fountain physics with depth shading
15. **Mirror-ball scroll** — Raytraced reflective sphere over scrolling chessboard
16. **3D Sinus field** — Comanche-style voxel height map (desert/water)
17. **Jelly picture** — Interference pattern morphing to photograph
18. **Vector part II** — Space battle scene with 3D ships
19. **End logo** — FC logo flash
20. **Credits** — Scrolling photos with credits text overlaid
21. **End scroller** — Long horizontal scroller (if not looping)

---

## Video Modes Used

| Mode | Description |
|---|---|
| Mode 13h (320×200×256) | Standard MCGA — used by most parts |
| Tweaked MCGA (320×400×256) | Double-scanned 400-line mode — used for opening credits, credits |
| EGA Mode 10h (640×350×16) | Standard EGA — used for Techno part |
| Tweaked EGA (320×200×256 planar) | Planar access tricks — used for plasma, opening scroller |
| Tweak mode (360×480 etc.) | Various CRTC hacks in TWEAK.ASM |

---

## Notable Technical Achievements for 1993

- Real-time 3D with flat and Gouraud shading (transparent "glenz" vectors)
- Music-synchronised animation throughout (using S3M row/order codes)
- Voxel heightmap renderer (precursor to Comanche-style terrain)
- Lens distortion with precomputed displacement maps
- Rotozoomer with bilinear-style sampling
- Plasma using summed sine lookup tables
- Per-scanline colour register cycling (copper-style effects)
- Full 3D city/spaceship scene from 3DS MAX data via custom converter
- EGA planar mode tricks for scrolling text wider than screen
- Independent binary parts loaded/freed sequentially

---

## Source Code Statistics

- ~35 separate demo part directories
- Mix of **x86 Assembly** (Watcom ASM / MASM syntax) and **Borland C**
- Shared utility library (DIS, TWEAK, FCP) reused across parts
- 3DS scene conversion pipeline (VISU/C/) for vector part assets
- Pre-computed data tables (SIN tables, lens maps, plasma tables) baked into EXEs via INCBIN
