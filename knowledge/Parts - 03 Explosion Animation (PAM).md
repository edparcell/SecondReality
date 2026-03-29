# Part 03: Opening Credits III — Praxis Explosion (PAM)

**Directory:** `original/PAM/`
**Output EXE:** `PAM.EXE`
**Coder:** TRUG
**Rendering:** TRUG

---

## Visual Effect

When the spaceship shrinks to a single pixel in the previous part, this part takes over and plays a pre-rendered animation of a massive ring-shaped explosion expanding outward toward the viewer — directly inspired by the "Praxis explosion" from Star Trek VI: The Undiscovered Country (1991). The explosion ring fills the screen and the screen flashes to white, then to the "Second Reality" logo.

---

## Technical Implementation

### Source Files

| File | Purpose |
|---|---|
| `ANIM.C` | Animation frame packer (development tool) |
| `VFLI.C` | FLI animation player for demo runtime |
| `ASMYT.ASM` | Optimised assembly routines |
| `COPPER.ASM` | Per-scanline palette/split effects |
| `INCLUDE.ASM` | Shared includes |
| `OUTTAA.C` | Output utilities |
| `PAL.INC` | Palette data (binary include) |
| `TWEAK.ASM` | VGA mode tweaking |

### Animation Format

The explosion is a pre-rendered animation stored as a `.FLI` file (`PRAX4.FLI`). FLI is a delta-compressed animation format originally by Autodesk Animator. Each frame stores only the pixels that changed from the previous frame.

The custom `VFLI.C` player decodes the FLI delta frames directly to video memory at playback time.

### ANIM.C — Frame Packer (Development Tool)

`ANIM.C` is a development-time tool that was used to create the compressed animation. It:
1. Reads the raw animation frames from `out.u` (uncompressed frame data)
2. For each frame, computes a delta against the previous frame
3. Outputs a run-length encoded stream where:
   - Positive byte N: N pixels follow that are different (copy them)
   - Negative byte -N: skip N pixels (unchanged)
   - Zero byte: end of frame
4. Writes output to `out.ani`

This custom delta compression achieved better ratios than generic FLI for this specific content (smooth expanding ring with large unchanged regions).

### Copper Effects

The `COPPER.ASM` routine handles:
- Split-screen scanline control for the explosion effect
- Per-frame palette updates to simulate the bright flash
- Smooth fade from explosion colours to white

### Assets

| File | Description |
|---|---|
| `PRAX4.FLI` | Pre-rendered Praxis explosion animation (FLI format) |
| `PAL.PAL` | Colour palette for the animation |

---

## Surprising Details

- The animation was pre-rendered (not real-time) — this was the only feasible approach for the quality level desired on 1993 hardware
- TRUG both coded the renderer and created the rendering, using custom ray-tracing or rendering software to create the explosion frames
- The `ANIM.C` packer aligns frame boundaries to 16-byte boundaries (`while ((ftell(out)&15) != 0) fputc(0, out)`) — likely for efficient DMA or segment alignment
- The FLI file is only 320×200×255 colours, but the effect feels cinematic due to the camera-shake-inducing scale of the ring
