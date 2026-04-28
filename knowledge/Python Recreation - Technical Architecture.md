# Python Recreation — Technical Architecture and Extension Guide

How the code works, how to run it, how to add new parts, and how to extend
the framework.

---

## Running the Demo

```bash
cd Python
pip install -r requirements.txt
python main.py
```

**Controls:**
- `ESC` — exit immediately
- `→` (Right Arrow) — skip to next part

**Resolution overrides (for development on non-4K hardware):**
```bash
SECOND_REALITY_WIDTH=1920 SECOND_REALITY_HEIGHT=1080 python main.py
SECOND_REALITY_WIDTH=960  SECOND_REALITY_HEIGHT=540  python main.py  # fast dev
SECOND_REALITY_FULLSCREEN=1 python main.py
```

**Music:**
The demo looks for MUSIC0.S3M and MUSIC1.S3M in `../original/MAIN/` relative
to the Python directory.  If not found, it logs a warning and runs silently.

---

## Directory Structure

```
Python/
├── main.py                # Entry point: builds part list, creates Runner, calls run()
├── requirements.txt       # pip dependencies
│
├── demo/                  # Core framework
│   ├── runner.py          # pygame init, OpenGL context, main loop, part sequencer
│   ├── dis.py             # DIS API: frame counter, music sync, copper callbacks
│   ├── music.py           # S3M playback + timing-based sync cues
│   └── part.py            # Abstract base class for all parts
│
├── parts/                 # One file per demo section
│   ├── p01_opening.py     # ALKU.EXE equivalent
│   ├── ...
│   └── p17_credits.py     # ENDLOGO + CRED + ENDSCRL equivalent
│
├── shaders/               # GLSL source files
│   ├── fullscreen_quad.vert   # Shared vertex shader (position + UV)
│   ├── plasma.frag
│   ├── lens.frag
│   ├── ... etc
│
├── utils/                 # Shared Python utilities
│   ├── sin_tables.py      # SIN1024 / SIN4096 numpy arrays + lookup functions
│   ├── math3d.py          # Matrix math, perspective, look_at
│   ├── palette.py         # 256-entry RGB palette, plasma_palette(), fire_palette()
│   └── font.py            # DemoFont (pygame-based), numpy_to_texture()
│
└── assets/                # HD art assets (textures, PNGs)
    └── README.md
```

---

## Framework Components in Detail

### Runner (`demo/runner.py`)

The `Runner` is the owner of:
- The pygame window and OpenGL context
- The main loop (runs at 60fps via `clock.tick(60)`)
- The part list and sequencer
- A shared fullscreen-quad VAO used by all shader-based effects
- The `DIS` instance

**Key public methods available to parts:**

```python
runner.clear(r, g, b, a)           # glClearColor + glClear
runner.draw_fullscreen_quad()      # draw NDC quad (for shader effects)
runner.compile_shader(vert, frag)  # returns GL program ID
runner.load_shader_files(v, f)     # load from shaders/ directory by filename
runner.width, runner.height        # screen dimensions
runner.aspect                      # width/height
```

**Main loop structure:**
```
while running:
    _handle_events()         ← ESC / → / window close
    current_part.render(dis, runner)
    pygame.display.flip()
    dis.tick()               ← frame counter, copper callbacks
    if current_part.is_done(dis):
        current_part.stop()
        advance to next part
    clock.tick(60)
```

---

### DIS (`demo/dis.py`)

Mirrors `original/DIS/DIS.H` exactly.  All parts should use the DIS API
rather than raw pygame or time calls.

```python
dis.frame           # int: total frames since demo start (read-only)
dis.get_mframe()    # int: frames since last dis.set_mframe(0) call
dis.set_mframe(n)   # reset the per-part frame counter to n
dis.waitb()         # int: frames since last waitb() call (vsync delta)
dis.exit()          # bool: True if ESC pressed
dis.musplus()       # int: music sync code (-100=running, -15..-2=exit cue, 0=stopped)
dis.musrow()        # int: current S3M row (0..63), used for beat sync
dis.set_copper(slot, fn)  # register per-frame callback (slot 0..3)
dis.partstart()     # call at part start: resets mframe, clears copper slots
```

**The music exit pattern** (used in almost every part):
```python
def render(self, dis, runner):
    # ... draw stuff ...
    a = dis.musplus()
    if 0 > a > -16:   # exit cue is active
        self.done()
```

**Beat-sync pattern** (used in Techno, Jelly):
```python
if dis.musrow() & 7 == 7:   # every 8th row = every "beat"
    self._flash = 1.0
```

**Copper callback pattern** (replaces original dis_setcopper):
```python
def my_copper():
    # Called every frame after render
    gl.glClearColor(...)   # or set a uniform, update palette, etc.

dis.set_copper(0, my_copper)
# Clear it when done:
dis.set_copper(0, None)
```

---

### Part Base Class (`demo/part.py`)

Every demo section inherits from `Part`:

```python
class Part:
    MAX_FRAMES: int | None = None  # auto-exit after this many frames (or None = music-only)

    def start(self, dis: DIS, runner: Runner) -> None:
        super().start(dis, runner)   # MUST call super — sets _start_frame, calls dis.partstart()
        # Load GL resources here

    def render(self, dis: DIS, runner: Runner) -> None:
        # Draw one frame here
        # Call self.done() or rely on MAX_FRAMES / musplus() for exit

    def is_done(self, dis: DIS) -> bool:
        # Default: True if _done flag set OR mframe >= MAX_FRAMES
        return self._done or (self.MAX_FRAMES and dis.get_mframe() >= self.MAX_FRAMES)

    def stop(self, dis: DIS, runner: Runner) -> None:
        # Clean up GL objects here
        gl.glDeleteProgram(self._prog)
        gl.glDeleteVertexArrays(1, [self._vao])
        # etc.
```

---

### Music Player (`demo/music.py`)

Wraps `pygame.mixer.music` for S3M playback.

**Important:** `MusicPlayer.load(0)` loads MUSIC0.S3M (intro, parts 1-5).
The runner currently only loads track 0 at startup.  To switch to MUSIC1.S3M
at the right point (after `PAM.EXE`), the runner needs to call:

```python
# In runner.py, when advancing from part index 2 (Explosion) to 3 (Logo):
if self._part_index == 3:  # About to start LogoReveal
    self._music.stop()
    self._music.load(1)
    self._music.play(start_row=42)  # bx=42 in original U2.ASM
```

This is not currently implemented — the demo plays MUSIC0 throughout.

---

## Adding a New Part

**1. Create `Python/parts/pXX_mypart.py`:**

```python
from __future__ import annotations
import OpenGL.GL as gl
from demo.part import Part
from demo.dis import DIS
from demo.runner import Runner

class MyPart(Part):
    MAX_FRAMES = int(15.0 * 60)   # 15 seconds max

    def start(self, dis: DIS, runner: Runner) -> None:
        super().start(dis, runner)
        self._prog = runner.load_shader_files("fullscreen_quad.vert",
                                               "myeffect.frag")

    def render(self, dis: DIS, runner: Runner) -> None:
        runner.clear()
        t = dis.get_mframe() / 60.0
        gl.glUseProgram(self._prog)
        gl.glUniform1f(gl.glGetUniformLocation(self._prog, "uTime"), t)
        runner.draw_fullscreen_quad()
        # Music exit:
        if 0 > dis.musplus() > -16:
            self.done()

    def stop(self, dis: DIS, runner: Runner) -> None:
        gl.glDeleteProgram(self._prog)
```

**2. Create `Python/shaders/myeffect.frag`:**

```glsl
#version 330 core
in vec2 vUV;
out vec4 fragColour;
uniform float uTime;
void main() {
    fragColour = vec4(vUV, abs(sin(uTime)), 1.0);
}
```

**3. Import and add to `main.py`:**

```python
from parts.pXX_mypart import MyPart
# In build_part_list():
return [
    ...,
    MyPart(),   # insert at desired position
    ...,
]
```

---

## Shader Conventions

All fullscreen/2D effects use the shared `fullscreen_quad.vert`.
It provides:
- `in vec2 aPos` (attrib 0): NDC position (-1..1)
- `in vec2 aUV` (attrib 1): UV (0..1, y=0 at bottom)
- `out vec2 vUV`: passed to fragment shader

**Standard uniform names (use these for consistency):**

| Name | Type | Meaning |
|------|------|---------|
| `uTime` | float | Seconds elapsed in this part |
| `uResolution` | vec2 | Render width, height in pixels |
| `uAspect` | float | width/height |
| `uScroll` | float | Horizontal scroll offset |
| `uFlash` | float | Beat-flash intensity [0..1] |
| `uAlpha` | float | Global opacity |
| `uSource` | sampler2D | Input texture for post-process effects |

---

## GL Resource Management Patterns

### Common pitfall: PyOpenGL `glGen*` returns a single int for n=1

```python
# glGenBuffers(1) returns an int, NOT a list:
vbo = gl.glGenBuffers(1)      # type: int
# glGenBuffers(3) returns a list of 3 ints:
v, c, e = gl.glGenBuffers(3)  # type: list[int]

# Deletion: always wrap scalars in a list:
gl.glDeleteBuffers(1, [vbo])
gl.glDeleteVertexArrays(1, [vao])
gl.glDeleteTextures([tex])    # no count argument for textures
gl.glDeleteProgram(prog)      # scalar, no list needed
```

### Framebuffer Object pattern

Used by `p10_lens.py` for the lens effect and should be used by `p14_voxel.py`:

```python
def _make_fbo(width, height):
    fbo = gl.glGenFramebuffers(1)
    tex = gl.glGenTextures(1)
    gl.glBindTexture(gl.GL_TEXTURE_2D, tex)
    gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGB, width, height, 0,
                    gl.GL_RGB, gl.GL_UNSIGNED_BYTE, None)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
    gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, fbo)
    gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0,
                               gl.GL_TEXTURE_2D, tex, 0)
    gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
    return int(fbo), int(tex)

# To render into it:
gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, fbo)
gl.glViewport(0, 0, w, h)
# ... draw ...
gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
gl.glViewport(0, 0, runner.width, runner.height)
```

### Uploading a texture from a numpy array

```python
# (H, W, 4) uint8 array → GL_TEXTURE_2D
from utils.font import numpy_to_texture
tex = numpy_to_texture(my_rgba_array)
```

### Uploading text as a texture

```python
from utils.font import DemoFont
font = DemoFont(size=int(runner.height * 0.06))
tex, w, h = font.make_texture("HELLO WORLD", (255, 200, 0))
# ... use tex as sampler2D ...
DemoFont.delete_texture(tex)   # in stop()
```

---

## Utility Reference

### `utils/sin_tables.py`

```python
from utils.sin_tables import SIN1024, COS1024, SIN4096, COS4096
from utils.sin_tables import isin, icos, isin4, icos4

# Integer lookup (period 1024, amplitude 1024):
v = isin(angle)          # angle wraps mod 1024
v = icos(angle & 1023)   # equivalent

# High-precision (period 4096, amplitude 4096):
v = isin4(angle & 4095)
```

### `utils/math3d.py`

```python
from utils import math3d

model = math3d.translation(x, y, z) @ math3d.rot_y(angle) @ math3d.scale(s, s, s)
proj  = math3d.perspective(fovy_deg=60, aspect=16/9, near=0.1, far=1000)
view  = math3d.look_at(eye, target, up)
mvp   = proj @ view @ model

# Upload to shader:
gl.glUniformMatrix4fv(loc, 1, gl.GL_FALSE, mvp.T.flatten())
# Note: .T.flatten() because OpenGL expects column-major, numpy is row-major
```

### `utils/palette.py`

```python
from utils.palette import Palette, plasma_palette, fire_palette, rainbow_palette

pal  = plasma_palette(3)        # palette index 0..5
dark = pal.fade(0.3)            # darken to 30%
mid  = pal.lerp(other_pal, 0.5) # blend two palettes

# Upload as 1D texture:
data = pal.as_texture_data()    # (1, 256, 3) uint8
tex  = numpy_to_texture(np.repeat(data, 1, axis=0).reshape(1, 256, 3)...)
```

---

## Performance Guide

### Target frame rates by resolution

| Resolution | Simple shaders (plasma, scroller) | Complex (voxel, many 3D objects) |
|------------|-----------------------------------|----------------------------------|
| 3840×2160 (4K) | 60fps | Need FBO downscale for voxel |
| 1920×1080 (1080p) | 60fps | 30-60fps depending on GPU |
| 1280×720 (720p) | 60fps | 60fps on most discrete GPUs |
| 960×540 (dev) | 60fps | 60fps easily |

### Profiling tools

```bash
# Frame timing:
pip install pyopengl-accelerate  # accelerates array passing

# GPU profiling:
# NVIDIA: nsight graphics / nvidia-smi
# General: renderdoc (free, cross-platform)
```

### When a part runs slow

1. Check if it uses any CPU-side per-frame computation that could move to GPU
2. For shader-heavy parts: profile in RenderDoc to see per-pass timing
3. Add `gl.glFinish()` around specific draw calls to isolate the bottleneck
4. Consider reducing internal resolution via FBO (see voxel fix above)

---

## Known Issues and TODOs in the Code

| File | Issue | Priority |
|------|-------|----------|
| `demo/runner.py` | Music doesn't switch from MUSIC0 to MUSIC1 between parts 2 and 3 | High |
| `demo/dis.py` | `exit()` still polls pygame event queue (race with runner) | Medium |
| `parts/p14_voxel.py` | No FBO downscale — will be very slow at 4K | Critical |
| `parts/p17_credits.py` | Fireworks RNG re-seeded from `int(t * 1000)` — will flicker | Low |
| `demo/music.py` | Timing table values are guesses — need calibration against actual S3M | High |
| All parts | PyOpenGL `glDeleteBuffers(n, list)` — numpy array safer than list | Low |
| `parts/p05_glenz.py` | All faces drawn with single colour — should cycle per-face | Medium |

---

## Dependencies and Compatibility

**Python:** 3.10+ (uses `int | None` syntax; `from __future__ import annotations`
in each file makes 3.8+ work too)

**pygame >= 2.3.0:** Required for `pygame.GL_CONTEXT_PROFILE_CORE` attribute.
pygame 2.x supports OpenGL 3.3 core profile contexts.

**PyOpenGL >= 3.1.7:** Stable.  Get `PyOpenGL-accelerate` too for better
performance with array uploads.

**numpy >= 1.24.0:** Required for float32/uint32 arrays.

**Pillow >= 10.0.0:** Only needed if loading image assets.  Not required for
the base recreation (everything is procedural).

**Common install issues:**
```bash
# On Linux, may need:
sudo apt install libsdl2-dev libgles2

# PyOpenGL-accelerate build failure (safe to skip):
pip install PyOpenGL PyOpenGL-accelerate || pip install PyOpenGL

# On M1/M2 Mac, pygame SDL2 path:
brew install sdl2 sdl2_mixer && pip install pygame
```
