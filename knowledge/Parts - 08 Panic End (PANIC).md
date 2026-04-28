# Part 08: Panic End (PANIC / PANICEND)

**Directory:** `original/PANIC/`
**Output EXE:** `PANICEND.EXE`
**Coder:** Wildfire

---

## Visual Effect

The screen image visibly "shrinks" toward the centre, getting smaller and smaller until it becomes a single pixel, then vanishes to black. This is a direct homage to the closing effect in the Finnish demo "Panic" (also by Future Crew, 1992). The music fades out simultaneously. There is then a pause of ~5 seconds.

---

## Technical Implementation

### Source Files

| File | Purpose |
|---|---|
| `SHUTDOWN.C` | Main logic for the shrink-to-point effect |
| `ASMYT.ASM` | Assembly helpers |
| `TWEAK.ASM` | VGA mode utilities |

### The Shrink Effect

The effect works by manipulating the VGA display start address and the pixel width register each frame to progressively show a smaller central region of the screen:

1. Each frame, decrease the visible area slightly
2. Adjust the display start address offset to keep the shrinking window centred
3. Modify the CRTC register for scan-line timing to compress vertically as well
4. Continue until width/height approach zero

The result is that the entire screen content (whatever was left over from the Techno part) shrinks to a point in the centre.

### Assets

| File | Description |
|---|---|
| `MONSTER.PAL` | Palette used during the panic shutdown effect |

---

## Surprising Details

- This is described in the SCRIPT as: "Panic style: screen shrinks to a point and music shuts off at the same time — pause of about 5 seconds"
- The homage to "Panic" was deliberate — Future Crew was effectively closing the chapter on their own earlier style before the demo's second half
- The 5-second silence was intentional dramatic effect, giving the viewer a moment of anticipation before the mountain scroll section begins
