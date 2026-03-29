# Python Recreation — Implementation Notes

Discoveries, surprises, workarounds, and deliberate departures made during the
Python/Pygame/OpenGL recreation of Second Reality.  Written immediately after
the first implementation pass so nothing is forgotten.

---

## 1. Music Sync: The Hardest Problem

The original demo's synchronisation between visuals and music is the central
technical challenge.  The entire part-exit system depends on `dis_musplus()`
returning specific negative values at exact moments.

**Original mechanism:**
`dis_musplus()` returned negative values tied to the S3M module's pattern/row
position.  When a specific row in a specific pattern was reached, the value
would enter the range `(-16, 0)`, and parts checked `if a < 0 and a > -16:
break` to exit.  This gave frame-perfect sync between music events and visual
transitions.

**The problem:**
`pygame.mixer.music` wraps SDL_mixer, which plays S3M files correctly but
**does not expose the current pattern/row position**.  You get elapsed time and
nothing else.

**What I did:**
Built a timing-table system in `demo/music.py`: a hard-coded list of
`(elapsed_seconds, cue_value)` pairs that fire exit cues at approximate
positions.  The values are estimates based on listening to the music and
eyeballing durations.

**The consequence:**
Visual transitions will drift against the music.  The further into the demo,
the worse it gets.  This is the single biggest fidelity gap in the recreation.

**The fix (for a future pass):**
Use `python-openmpt` (libopenmpt Python bindings).  `libopenmpt` exposes
`openmpt.module.get_current_pattern()` and `get_current_row()`, which is
exactly what the original DIS used.  Once that's in place the timing table
can be replaced with real row-matching.

```python
# Future: replace MusicPlayer._get_position() with:
import openmpt
mod = openmpt.module.Module(open("MUSIC1.S3M", "rb"))
row = mod.get_current_row()     # 0..63
pat = mod.get_current_pattern() # 0..N
```

---

## 2. Glenz XOR Blending Has No Direct OpenGL Equivalent

**Original:**
The Glenz effect worked by XOR-ing palette indices.  Face A had colour index 3,
face B had colour index 5, and where they overlapped the pixel got index `3 XOR 5 = 6`.
This produced a specific semi-transparent "crystalline" appearance because the
palette was designed with this in mind — the XOR of two colours was always a
lighter, brighter shade.

**OpenGL reality:**
OpenGL's blend modes operate on linear RGB values, not palette indices.
There is no `GL_XOR` blend equation (it exists for bitmasks in the old
`glLogicOp` API, but that only works with the write mask, not colour blending).

**What I used:**
`GL_SRC_ALPHA, GL_ONE` (additive blending).  Where faces overlap, their colours
add together, which produces a bright/glowing appearance.  This is the closest
qualitative match — overlapping faces become brighter — but the specific hue
shifts from XOR are lost.

**Better approaches (future):**
- Render the scene to an offscreen 256-entry palette texture, do the XOR on
  integer palette indices (CPU-side or compute shader), then map to RGB.
  This is faithful but complex.
- Use screen-blend: `gl_FragColor * (1 - dst_color) + dst_color`.
  This gives a lighter, more saturated result than additive and is closer
  to the XOR palette feel.

---

## 3. FBO Required for Lens Effect

**Original:**
The lens distortion was computed by reading the VGA framebuffer at 0xA0000
directly.  The CPU wrote the background, then read the background back through
a displacement table to produce the lens output.  Reading and writing the same
framebuffer in one pass was fine because the displacement was always forward
(reading pixels not yet overwritten in that scanline pass).

**OpenGL reality:**
You cannot read from the framebuffer you are currently writing to.  Reading
`GL_READ_FRAMEBUFFER` while drawing to `GL_DRAW_FRAMEBUFFER` is the default
setup but has undefined behaviour for same-texture reads in GLSL.

**What I did:**
Used a two-pass approach with a Framebuffer Object (FBO):
1. Render background to an FBO texture (`lens_bg.frag`)
2. Bind that texture as `uSource` and run `lens.frag` as a fullscreen pass
   reading from the texture and writing to the default framebuffer

This works perfectly and is the standard GPU approach, but it costs one extra
fullscreen render pass plus FBO memory (3840×2160×3 bytes ≈ 24MB).

---

## 4. Voxel Shader Performance Will Not Run at 60fps at 4K

**The problem:**
The `voxel.frag` shader performs a ray march with up to 800 iterations per
pixel.  At 3840×2160 that is 8,294,400 pixels × 800 iterations = **6.6 billion
shader operations per frame**.  Even a top-end GPU (RTX 4090 at ~100 TFLOPS)
cannot do this at 60fps.

**What will actually happen:**
The GPU will either stall the frame (presenting at 2-5fps), or the driver
will kill the long-running shader (TDR on Windows, GPU reset on Linux).

**The fix before running:**
Add a render resolution for the voxel part.  Render at 960×540 (1/4 linear)
or 1280×720 and upscale with bilinear filtering to fill the screen.  The
voxel/heightmap look actually benefits from slight softness at scale.

```python
# In p14_voxel.py render():
VOXEL_SCALE = 0.25  # render at 25% res, upscale
vw = int(runner.width  * VOXEL_SCALE)
vh = int(runner.height * VOXEL_SCALE)

gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self._fbo)
gl.glViewport(0, 0, vw, vh)
# ... draw voxel shader ...
gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
gl.glViewport(0, 0, runner.width, runner.height)
# blit FBO to screen with bilinear upscale
```

Also, the adaptive step size in `voxel.frag` (`stepSize *= 1.005` at distance)
helps but isn't enough at 4K.  Reduce the inner loop iteration count to 300-400
and increase the base step size from 1.5 to 2.5.

---

## 5. Pre-Recorded Path Data Replaced with Approximations

**Lens + Rotozoomer (`LENS/MAIN.C`):**
`pathdata1[]` and `pathdata2[]` were recorded during development using a
special `#ifdef SAVEPATH` build that wrote the physics simulation to disk.
The final demo replays these files frame-by-frame.  The paths are not
reproducible from the code alone without running the original physics with the
same initial conditions.

**What I did:**
Approximated with layered sinusoids that capture the "bouncing lens" character:
```python
lx = 0.5 + sin(t * 1.7) * 0.25 + sin(t * 0.4) * 0.1
ly = 0.5 + cos(t * 1.3) * 0.2  + cos(t * 0.6) * 0.08
```

This produces plausible motion but won't match the original recording exactly.

**Better approach:**
Extract the raw `pathdata1.dat` and `pathdata2.dat` files from the original
demo binary (they're linked in by DOOBJ), parse them as signed 16-bit integers,
and replay them.  The path is 2 bytes × 2 coords × N frames, likely packed
into a `.OBJ` linkable file.

---

## 6. The Spaceship is Completely Different from the Original

**Original (`VISU/`):**
Loaded `.ASC` (Autodesk Animator ASCII) geometry files — actual 3D models of a
city, spaceship, and environment.  Also loaded `.VUE` camera animation files
(pre-animated flythrough path) and `.MAT` material definitions.  The renderer
did flat/Gouraud polygon fill with Z-sort insertion sort.  The result was a
recognisable futuristic cityscape with a specific architectural style.

**HD recreation:**
Generated a procedural grid of identical rectangular boxes.  The visual
character is completely wrong — it looks like a generic demo city, not the
original Finnish-designed scene.

**How to fix:**
The `.ASC` files in `original/VISU/` contain the original geometry.  Writing an
ASC parser is straightforward (it's ASCII text).  The geometry could be:
1. Parsed from `.ASC` directly in Python (the format is documented)
2. Converted to OBJ using Blender (open .ASC, export .OBJ)
3. Loaded with `trimesh` or `pywavefront`

See `original/VISU/C/MAIN.C` `readasc()` function for the parser logic.

---

## 7. The Explosion is Completely Different from the Original

**Original (`PAM/`):**
An FLI animation file (`ANIM.FLI`) played back frame by frame — a
specifically-crafted explosion sequence created in an animation tool.  The
original had a distinctive look with a bright white flash expanding to orange
and red, specific smoke behaviour, and a debris pattern that was hand-crafted
rather than physically simulated.

**HD recreation:**
A generic particle explosion with gravity, drag, and fire colour gradient.
Functionally similar but aesthetically very different.

**How to fix:**
The FLI format is documented and decodable.  `original/PAM/ANIM.C` is the
original packer.  A Python FLI decoder could extract the original frames as
a PNG sequence, which could then be upscaled (via AI upscaler or bilinear) and
played as a texture atlas in the HD version.

Alternatively, the explosion could be recreated as a proper particle simulation
with billboarded quads, normal-mapped sprites, and volumetric smoke.

---

## 8. Event Queue Ownership Between Runner and Parts

**The problem:**
The original `dis_exit()` worked by checking a flag set by the ISR (interrupt
service routine) when any key was pressed.  There was no question of "who owns
the event".

In pygame, `event.get()` consumes events from a global queue.  The
`Runner._handle_events()` drains KEYDOWN and QUIT.  If a `Part` also calls
`dis.exit()` (which calls `pygame.event.get()`), it might consume events that
the Runner hasn't seen yet.

**Current state:**
`DIS.exit()` calls `pygame.event.get(pygame.KEYDOWN)` — it uses the type filter
so it only consumes KEYDOWN events.  The Runner also calls
`pygame.event.get()` (all events) in `_handle_events()`.  There's a risk of
KEYDOWN being consumed by either before the other sees it.

**Safe fix:**
Don't call `pygame.event.get()` in `DIS.exit()`.  Instead, have Runner set
`dis._exit_requested = True` in `_handle_events()` when ESC is pressed, and
have `dis.exit()` just read that flag.  The current code mostly does this but
`DIS.exit()` still polls the queue independently.

---

## 9. PyOpenGL `glDeleteBuffers` API Quirks

**The problem:**
PyOpenGL's `glDeleteBuffers(n, buffers)` expects a list or numpy array for
`buffers`.  When `glGenBuffers(1)` returns a single Python integer (not a
list), you must wrap it:

```python
# WRONG — will crash or silently fail:
gl.glDeleteBuffers(1, self._vbo)

# CORRECT:
gl.glDeleteBuffers(1, [self._vbo])
```

Similarly, `glDeleteVertexArrays(1, vao)` needs `[vao]`.  And
`glDeleteTextures([tex])` takes a list (no count argument — PyOpenGL infers
it).  The API inconsistency across GL object types is a frequent source of bugs.

**Also:** `glDeleteBuffers(4, list(self._vbos))` in `p05_glenz.py` passes a
Python list which should work, but a numpy array is safer:
```python
gl.glDeleteBuffers(4, np.array(list(self._vbos), dtype=np.uint32))
```

---

## 10. The Plasma Interlaced-Field Structure is Simplified

**Original:**
The plasma was rendered in two passes per frame: odd scan-lines with parameters
`k1/k2/k3/k4`, even scan-lines with `l1/l2/l3/l4`.  This interlacing (a legacy
of CRT scan-line rendering) gave the plasma a distinctive shimmering quality
because adjacent rows used slightly different parameter sets.

**HD recreation:**
The GLSL shader uses a single parameter set for all pixels.  The two-field
shimmer is absent.

**How to add it:**
In `plasma.frag`, branch on `int(vUV.y * resolution.y) % 2`:

```glsl
uniform float uResolutionY;
// ...
int scanline = int(vUV.y * uResolutionY);
float v;
if (scanline % 2 == 0) {
    v = plasma(vUV.x, vUV.y, uP1, uP2, uP3, uP4);        // even field
} else {
    v = plasma(vUV.x, vUV.y, uK1, uK2, uK3, uK4);        // odd field
}
```

Add `uK1..uK4` uniforms driven by a separate parameter track in `p11_plasma.py`.

---

## 11. Dot Tunnel Phase Transitions Are Approximate

**Original (`DOTS/MAIN.C`):**
The shuffle order `dottaul[]` was a specific pre-computed permutation.  Phase
transitions happened at exact frame counts, with dots lerping toward their new
target positions independently.  The tunnel phase used `sin1024[frame&1023]/8`
for the radius, which creates a specific pulsing tunnel shape tied to the
integer sine table.

**HD recreation:**
Used a Fisher-Yates shuffle with seed `0x1234` — this gives a deterministic
but different order than the original.  The `SIN1024` table is accurately
ported and the tunnel formula `a = SIN1024[frame & 1023] / 1024.0 * 0.8 + 0.3`
is faithful to the original.  Phase end frames match the original exactly.

The main departure: lerp speed is constant (0.06 per frame) whereas the
original may have used different rates per phase.

---

## 12. The Credits Photographs Are Missing

**Original (`CREDITS/MAIN.C`):**
18 actual photographs of Future Crew members were embedded in the demo,
displayed with team member names overlaid in the bitmap font.  The photos were
IFF ILBM bitmaps converted to Mode 13h palette format.

**HD recreation:**
Plain text cards with name + role.  This is the most artistically significant
gap in the entire recreation — the credits photos are a core part of the demo's
emotional impact.

**Options:**
1. Extract and decode the original LBM photos (they are in `original/CREDITS/`)
   and upscale with a super-resolution tool (Real-ESRGAN, waifu2x, etc.)
2. Commission new portrait artwork for each member
3. Leave as stylized text cards — this is a deliberate artistic choice and is
   not necessarily wrong

The LBM files are at: `original/CREDITS/*.LBM` (verify with `ls`)

---

## 13. Python Type Union Syntax Requires Python 3.10+

Several files use `int | None` syntax:
```python
MAX_FRAMES: int | None = None
```

This syntax was introduced in Python 3.10.  On Python 3.9 this raises a
`TypeError`.  Change to:
```python
from typing import Optional
MAX_FRAMES: Optional[int] = None
```

Or use `from __future__ import annotations` at the top of each file (which
defers annotation evaluation and makes the syntax work on 3.8+).  All files
do have `from __future__ import annotations` at the top, so this is already
handled — but it's worth noting.

---

## 14. The DIS Copper Rate Mismatch

**Original:**
The DIS copper callbacks fired from the VBlank interrupt at exactly 70Hz
(the standard VGA refresh rate).  The original parts tuned their palette
effects to 70Hz timing.

**HD recreation:**
`DIS.tick()` fires the copper callbacks once per `Runner.run()` frame iteration,
which targets 60fps via `clock.tick(60)`.  Copper-driven effects (palette
cycling, beat flash) will run 14% slower than intended.

This is unlikely to be perceptible for most effects, but beat-sync effects like
the Techno bar flash (`p07_techno.py`) will drift slightly relative to the
music.

---

## 15. The `STARTMUS.EXE` and `START.EXE` Setup Are Skipped

**Original:**
`U2.ASM` runs `STARTMUS.EXE` first (loads and starts music) then `START.EXE`
(the setup menu: sound card selection, quality, looping).  These negotiate the
`DIS` message area 3 to pass configuration to subsequent parts.

**HD recreation:**
These are skipped.  The runner hard-codes pygame.mixer with 44100Hz stereo.
The sound card detection, quality settings, and the original setup menu UI are
not present.  This is intentional — the HD version just uses the system audio.

---

## 16. Hidden Part DDSTARS Not Implemented

The original demo had a hidden `DDSTARS.EXE` (Desert Dream stars effect)
accessible via a keypressed sequence.  The part list in `main.py` does not
include it.  It could be added as an optional part triggered by a key combo.

---

## 17. The `dis_exit()` Semantics Changed

**Original:**
`dis_exit()` returned 1 if *any* key was pressed — it was a "has the user
requested exit" check used inside part loops.

**HD recreation:**
`dis.exit()` returns `True` if ESC was pressed.  Arrow-right skips to the next
part (handled by `Runner._handle_events()` calling `current_part.done()`).
Any other key does nothing.

This is probably better UX for the HD version, but it means parts cannot be
exited with "any key" — you must press ESC or right arrow.  Parts that poll
`dis.exit()` internally will only respect ESC.

---

## Summary: Fidelity Gaps (Most to Least Significant)

| Gap | Impact | Fix Difficulty |
|-----|--------|---------------|
| Music sync (row-level precision) | High — transitions drift | Medium: add libopenmpt |
| Spaceship geometry (.ASC files) | High — visually wrong | Medium: write ASC parser |
| Credits photographs | High — emotional impact | Low: decode LBM + upscale |
| Explosion (was FLI animation) | Medium — different aesthetic | Low: decode FLI |
| Glenz XOR blending | Medium — colour behaviour differs | Hard: need palette shader |
| Plasma interlaced fields | Low — subtle shimmer missing | Easy: add odd/even branch |
| Pre-recorded lens path | Low — motion is plausible | Low: extract from binary |
| Voxel 4K performance | Critical if run at full res | Easy: add FBO downscale |
| Dot tunnel shuffle order | Very low | Very low |
