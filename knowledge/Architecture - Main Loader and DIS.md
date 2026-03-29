# Architecture: Main Loader and DIS System

## Overview

The demo's execution is controlled by two interlocking systems:
1. **U2.EXE / U2.ASM** — the main loader and sequencer
2. **DIS** — Demo Interrupt Server, a shared runtime services layer

---

## U2.EXE — Main Loader (`original/MAIN/U2.ASM`)

`U2.EXE` is the first program the user runs. It is written entirely in x86 assembly (MASM syntax, `.386` mode) and performs the following:

### Startup Sequence

1. **Set stack** at CS:400h (1K stack hidden at the start of the code segment)
2. **Store PSP** (Program Segment Prefix) and release unused memory
3. **Save interrupt vector table** (zero page 256×4 bytes) for clean restoration at exit
4. **Check system requirements** via `checkall`:
   - At least 570,000 bytes (≈557K) of conventional memory free
   - 386 or higher CPU (tests stack-push behaviour and `sgdt` instruction)
   - VGA adapter (BIOS function 1A00h, checks BL ≥ 7)
5. **Initialise DIS** — install the interrupt-based services
6. **Initialise file packing** — set up access to the compressed `REALITY.FC` pack file
7. **Run `START.EXE`** — the setup menu (sound card selection etc.)
8. **Initialise STMIK** sound player with the selected output mode
9. **Load and start music** via `STARTMUS.EXE`

### Part Sequencer

After startup, U2.EXE loops through a fixed part list:

```asm
exe1    db 'ALKU.EXE',0        ; Opening credits I
exe2    db 'U2A.EXE',0         ; Opening credits II (ship)
exe3a   db 'PAM.EXE',0         ; Opening credits III (explosion)
exe3    db 'BEGLOGO.EXE',0     ; Logo reveal
exe4    db 'GLENZ.EXE',0       ; Glenz vectors
exe5    db 'TUNNELI.EXE',0     ; Dot tunnel
exe6    db 'TECHNO.EXE',0      ; Techno bars
exe7    db 'PANICEND.EXE',0    ; Panic end
exe9    db 'MNTSCRL.EXE',0     ; Mountain scroll
exe1112 db 'LNS&ZOOM.EXE',0   ; Lens + Rotozoomer (combined)
exe1314 db 'PLZPART.EXE',0     ; Plasma + Plasma cube
exe15   db 'MINVBALL.EXE',0    ; Mini vector balls
exe16   db 'RAYSCRL.EXE',0     ; Mirror-ball scroll
exe17   db '3DSINFLD.EXE',0    ; 3D sinus field (Comanche)
exe18   db 'JPLOGO.EXE',0      ; Jelly picture / interference
exe19   db 'U2E.EXE',0         ; Vector part II (space battle)
exe2021 db 'ENDLOGO.EXE',0     ; End logo flash
exe22   db 'CRED.EXE',0        ; Credits
exe23   db 'ENDSCRL.EXE',0     ; End scroller
exehid  db 'DDSTARS.EXE',0     ; Hidden part (Desert Dream Stars)
```

Parts are grouped into 5 sections controlled by `whattorun` bitmask:
- Bit 0: Intro parts (ALKU, U2A, PAM)
- Bit 1: Logo + effects I (BEGLOGO through PANICEND)
- Bit 2: Effects II (MNTSCRL through JPLOGO)
- Bit 3: Vector part (U2E)
- Bit 4: Endings (ENDLOGO, CRED, ENDSCRL)
- Bit 7: Hidden (DDSTARS)

The user can start from the middle of the demo by passing a number (2–5) on the command line.

### `partexecute` Procedure

Before executing each part:
1. Checks if Ctrl is held down (if so, skip this part)
2. Calls `execute` to load and run the EXE
3. Flushes the keyboard buffer
4. Resets copper interrupt vectors to `copper_intretf` (no-op return)

### Memory Management

- Each part EXE is loaded into memory, executed to completion, then freed
- STMIK music player lives in a fixed segment (`stmikseg`) throughout
- Music module segment tracked in `moduleseg`
- Music restarts between major sections via `restartmus` (reloads `STARTMUS.EXE`)
- Minimum free memory checked via DOS interrupt 21h/48h

### Error Handling

Comprehensive error messages are displayed for:
- Sound card init failure
- Insufficient conventional memory (<570K)
- Insufficient EMS memory for music (with SB cards)
- CPU below 386
- No VGA adapter
- Running under Windows (detected via `windir` environment variable)
- Missing EXE files
- Internal subfile load failure

### Music Fading / Looping

- `fademusic` gradually decrements the volume in the S3M module header
- If looping is enabled, the sequencer restarts from the beginning after completing all parts
- Music is re-initialised at the start of each loop

---

## DIS — Demo Interrupt Server (`original/DIS/`)

DIS is a small resident interrupt-based service layer. It is embedded directly into `U2.ASM` via `include ..\dis\disint.asm`.

### Interface (`original/DIS/DIS.H`)

```c
int  dis_version(void);       // Init DIS for this part; returns version or 0 if missing
int  dis_indemo(void);        // 1 = running inside demo, 0 = standalone
int  dis_waitb(void);         // Wait for VBlank; returns frames since last call
int  dis_exit(void);          // Returns 1 if any key pressed (exit signal)
void dis_partstart(void);     // Auto-init; exits to DOS if DIS not found
void *dis_msgarea(int n);     // Access shared 64-byte message area (0..3)
int  dis_muscode(int);        // Get music sync code (pattern)
int  dis_musplus(void);       // Get music sync code (signed)
int  dis_musrow(int);         // Get music row number
void dis_setcopper(int n, void (*fn)(void)); // Register VBlank/HBlank callback
void dis_setmframe(int f);    // Set music frame counter
int  dis_getmframe(void);     // Get music frame counter
int  dis_sync(void);          // Get sync counter
```

### Message Areas

Four 64-byte shared memory areas used for inter-part communication:
- Area 0: Current part use (general)
- Area 1: VGA state for EGA 320×200×16 mode
- Area 2: VGA state for MCGA 320×200×256 mode
- Area 3: Used by START.EXE / U2.EXE for sound card settings

Contents of area 3 (set by START.EXE):
- `[bx+0]`: exit flag (-1 = user pressed ESC in menu)
- `[bx+2]`: sound card type (1=SB, 2=SBPro, 3=GUS)
- `[bx+4]`: sound quality (0=poor, 1=standard, 2=high)
- `[bx+6]`: looping flag

### The "Copper" System

Named after the Amiga's copper chip, the DIS copper is an interrupt routine that fires:
- Once per scanline (if a high-resolution copper is registered)
- At top/bottom of frame (standard usage)
- During retrace

This allows parts to do per-scanline palette changes, split-screen effects, and other raster tricks without explicit polling in the main loop.

### Music Synchronisation

The STMIK player exposes sync codes that DIS can read:
- `dis_musplus()` — returns negative values counting down to 0 at sync points, then positive thereafter
- `dis_musrow()` — returns the current S3M pattern row
- `dis_getmframe()` — returns an absolute frame count driven by the music timer

Parts use these to synchronise visual events to the music, e.g.:
```c
while(!dis_exit() && dis_musplus() < -6) ;  // wait for music cue
```

---

## STMIK Sound System (`original/MAIN/STMIKA.INC`, `STMIK.H`)

STMIK is embedded in the `U2.EXE` code segment via `include stmika.inc`. It handles:

- S3M module playback (ScreamTracker 3 format)
- Output modes: `_zoutputmode` variable
  - 7 = No sound
  - 1 = SoundBlaster (mono)
  - 5 = SoundBlaster Pro (stereo, double mix speed)
  - 2 = Gravis UltraSound
- `_zmixspeed`: mixing rate (12000, 16000, or 20000 Hz depending on quality)
- `_zpollmix`: set to 1 to enable polling-based mixing (used during demo)
- EMS memory management for SB music buffers (`_zemspageframe`, `_zemspagehandle`)

Key STMIK entry points called by U2.ASM:
- `_zinit` — initialise sound hardware
- `_zplaysong` — start playback
- `_zsoundoff` / `_zsoundon` — mute/unmute
- `_zstopsong` — stop playback
- `_zshutup` — silence all channels
- `_zloadinstrument` — load GUS instrument
- `_zsizegusmem` — query GUS memory

---

## File Packing System (`original/MAIN/PACKING.INC`, `FCP/`)

All part EXE files are packed into a single `REALITY.FC` archive. The `original/FCP/` tools handle this:

- `PACK.C` — creates the packed archive
- `UNPACK.ASM` — decompressor stub (embedded in part loader)
- `PRINT.C` — utility printer

The pack format uses simple run-length / delta compression. The `PACKING.INC` file contains a directory of packed files that the loader references to locate and decompress each part on demand.

---

## Startup Menu (`original/MAIN/START.C`, `MENU.C`)

`START.EXE` presents a VGA text-mode menu with the following options:
- **Soundcard**: No sound / SoundBlaster mono / SoundBlaster Pro stereo / Gravis UltraSound 512K
- **Sound quality**: Poor (12kHz) / Standard (16kHz) / High (20kHz)
- **Demo looping**: Disabled / Enabled (skips end scroller)

The menu detects Windows and refuses to run under it.

Results stored in DIS message area 3 for the main loader to read.

---

## Surprising Details

- The `CODE`, `DESIGN`, `IDEAS`, `SCRIPT`, and `VECSCR` files in the root are internal development documentation — design notes written in Finnish describing the intended visual effects, giving fascinating insight into the creative process.
- The SCRIPT file describes the demo partly in Finnish and notes that music synchronisation was designed to match SFX (surround sound effects from behind for the spaceship approach).
- `U2.EXE` has a hidden copyright message embedded in the stack area at the start of the code segment: `"SECOND REALITY (beta) Copyright (C) 1993 The Future Crew"`.
- The parts mask system allows starting the demo from any section, which was used during development. Running `SECOND 2` would skip the intro sequence.
- There is a hidden "Desert Dream Stars" part (`DDSTARS.EXE`) triggered by `whattorun` bit 7, never shown in a normal run. It is a tribute to another group's (Desert Dream) demo.
