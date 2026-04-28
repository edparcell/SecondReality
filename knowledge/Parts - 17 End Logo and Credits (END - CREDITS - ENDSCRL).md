# Parts 17–19: End Logo, Credits, End Scroller

---

# Part 17: End Logo Flash (ENDLOGO / END + ENDPIC)

**Directory:** `original/END/`, `original/ENDPIC/`
**Output EXE:** `ENDLOGO.EXE`
**Coder:** Wildfire / PSI

## Visual Effect

After the space battle fades to black, the "Future Crew" logo flashes up — first as a white silhouette, then with colours fading in. The logo "thumps" to the music beat. Multiple images flash in sequence.

## Assets

| File | Description |
|---|---|
| `FUTURE_8.LBM` | Future Crew logo (8-colour variant) |
| `NUTS.LBM` | Additional graphic |
| `PIC.LBM` | Picture display |
| `SRTITLE.LBM` | Second Reality title reuse |

## Technical Notes

- `END.C` / `BEG.C` use the same `READP.C` packed picture reader
- The `ASM.ASM` in both `END/` and `ENDPIC/` provide mode switching and blitting helpers

---

# Part 18: Credits Screen (CRED / CREDITS)

**Directory:** `original/CREDITS/`
**Output EXE:** `CRED.EXE`

## Visual Effect

A credits sequence displaying photos of the demo sections alongside the names of the people responsible for each part. Photos slide in from below in a wobbly/bouncy manner (similar to the logo reveal), stay on screen while credit text is displayed, then slide out upward. 18 photos cycle through, each with associated names.

## Implementation

### Source Files

| File | Purpose |
|---|---|
| `MAIN.C` | Main loop: picture show, text overlay, transitions |
| `INCLUDE.ASM` | Shared includes |
| `INCLUD2.ASM` | Secondary includes |
| `TWEAK.ASM` / `TWEAK.H` | Tweaked VGA mode |
| `FONA.INC` | Font data |
| `TEST.INC` | Test data |

### Credits Sequence (from MAIN.C)

Each picture + credit entry:

| Picture | Credits |
|---|---|
| PIC01 | GRAPHICS - MARVEL / MUSIC - SKAVEN / CODE - WILDFIRE |
| PIC02 | GRAPHICS - MARVEL / MUSIC - SKAVEN / CODE - PSI |
| PIC03 | GRAPHICS - MARVEL / MUSIC - SKAVEN / CODE - WILDFIRE / ANIMATION - TRUG |
| PIC04 | GRAPHICS - PIXEL |
| PIC05 | GRAPHICS - PIXEL / MUSIC - PURPLE MOTION / CODE - PSI |
| PIC05B | MUSIC - PURPLE MOTION / CODE - TRUG |
| PIC06 | MUSIC - PURPLE MOTION / CODE - PSI |
| PIC07 | MUSIC - PURPLE MOTION / CODE - PSI |
| PIC08 | GRAPHICS - PIXEL / MUSIC - PURPLE MOTION |
| PIC09 | GRAPHICS - PIXEL / MUSIC - PURPLE MOTION / CODE - TRUG / RENDERING - TRUG |
| PIC10 | GRAPHICS - PIXEL, SKAVEN / MUSIC - PURPLE MOTION / CODE - PSI |
| PIC10B | GRAPHICS - PIXEL, SKAVEN / MUSIC - PURPLE MOTION / CODE - PSI |
| PIC11 | MUSIC - PURPLE MOTION / CODE - WILDFIRE |
| PIC12 | MUSIC - PURPLE MOTION / CODE - WILDFIRE |
| PIC13 | MUSIC - PURPLE MOTION / CODE - PSI |
| PIC14 | GRAPHICS - PIXEL / MUSIC - PURPLE MOTION / CODE - TRUG / RENDERING - TRUG |
| PIC14B | MUSIC - PURPLE MOTION / CODE - PSI |
| PIC15 | GRAPHICS - MARVEL / MUSIC - PURPLE MOTION / CODE - PSI |
| PIC16 | MUSIC - SKAVEN / CODE - PSI |
| PIC17 | GRAPHICS - PIXEL / MUSIC - PURPLE MOTION |
| PIC18 | GRAPHICS - PIXEL / MUSIC - PURPLE MOTION / CODE - WILDFIRE |

### Screen Transition

Each photo uses a "split-screen zoom" transition (`screenin` function):
1. Photo is displayed at 160×100 pixels (half-res)
2. Split screen point starts at 200 (off-screen)
3. Animated loop: `tw_setsplit()` + `tw_setstart()` for pixel-smooth scrolling
4. The split line moves from 200 down to the centre, revealing the photo
5. After display time, split moves back up

This uses Mode X / tweaked VGA split-screen capability to show the photo in the bottom half while the top half shows something else.

### Font

The font is loaded from `INCLUD2.ASM` — a 48-character bitmap font stored as embedded data (uppercase A-Z, digits, punctuation). Characters are rendered at 32 pixels tall using `font[FONAY][1500]`.

### Assets (CREDITS/PICS/)

18 LBM pictures (PIC01 through PIC18, plus variants PIC05B, PIC10B, PIC14B) — screenshots/artwork from each demo section.

---

# Part 19: End Scroller (ENDSCRL)

**Directory:** `original/ENDSCRL/`
**Output EXE:** `ENDSCRL.EXE`
**Coder:** (unclear, likely PSI or Wildfire)

## Visual Effect

A long horizontal text scroller running across the bottom of the screen with greetings to other demo groups, thanks, and messages from the Future Crew members. Disabled if looping mode is selected.

## Source Files

| File | Purpose |
|---|---|
| `MAIN.C` | Scroller main loop |
| `ASMYT.ASM` | Assembly helpers |
| `FONA.INC` | Font data for scroller text |

## Assets

| File | Description |
|---|---|
| `FONA.LBM` | Scroller font graphic |

---

## Surprising Details Across End Parts

- `CREDITS/MAIN.C` has a `memmove` that shifts all 21 picture's palette data by `16*3+16` bytes — adjusting for EGA palette format stored in the LBM vs the expected MCGA format
- The first 10 palette entries of each credits picture are overwritten with a smooth grey ramp (`a*3+0 = a*3+1 = a*3+2 = 7*a`) — ensuring consistent text legibility overlay
- The credits pictures were taken as screenshots from the actual demo parts, making the credits section a visual tour-replay of what was just seen
- `INCLUD2.ASM` vs `INCLUDE.ASM` being two separate include files suggests the credits part was developed more independently
