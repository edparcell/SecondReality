# Python Recreation — Next Steps and Asset Improvements

Concrete improvements ordered from most impactful to most optional.
Each entry describes the current state, what the improvement looks like,
and how to implement it.

---

## Critical: Performance Fixes Before Running

### Voxel Landscape — Internal Resolution Downscale

**Why urgent:** The `voxel.frag` shader will crash or cause a GPU TDR timeout
at 3840×2160.  It must run at a reduced internal resolution before the first
test run.

**Implementation in `Python/parts/p14_voxel.py`:**

```python
VOXEL_SCALE = 0.25  # render at 960×540, upscale to 4K

def start(self, dis, runner):
    super().start(dis, runner)
    vw = int(runner.width  * VOXEL_SCALE)
    vh = int(runner.height * VOXEL_SCALE)
    self._prog = runner.load_shader_files("fullscreen_quad.vert", "voxel.frag")
    self._blit_prog = runner.load_shader_files("fullscreen_quad.vert",
                                                "blit_nearest.frag")
    self._fbo, self._fbo_tex = self._make_fbo(vw, vh)
    self._voxel_w = vw
    self._voxel_h = vh

def render(self, dis, runner):
    # Render voxel at low res
    gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self._fbo)
    gl.glViewport(0, 0, self._voxel_w, self._voxel_h)
    gl.glClear(gl.GL_COLOR_BUFFER_BIT)
    # ... draw voxel ...
    gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
    gl.glViewport(0, 0, runner.width, runner.height)
    # Upscale blit
    gl.glUseProgram(self._blit_prog)
    gl.glBindTexture(gl.GL_TEXTURE_2D, self._fbo_tex)
    runner.draw_fullscreen_quad()
```

Also reduce the ray march step count in `voxel.frag`:
- Change `maxDist` from 800 to 500
- Change base `stepSize` from 1.5 to 3.0
- Remove the inner distance-based step increases (they complicate the loop)

A simple blit shader (`shaders/blit_nearest.frag`) is just a texture lookup
with a sampler2D uniform — already similar to the lens_bg shader.

---

## Tier 1: High Impact, Relatively Straightforward

### 1. Decode and Use the Original Credits Photos

**Current:** Text-only credit cards.
**Target:** Actual team member photographs from the original demo.

**The photos exist in:** `original/CREDITS/*.LBM` (IFF ILBM format, 256-colour)

**Steps:**
1. Write a minimal IFF ILBM decoder (or use the `ilbmtoppm` tool from
   `netpbm`, or Python's `Pillow` with the IFF plugin from `pillow-iiff`)
2. Decode each LBM to RGB array
3. Apply an upscaling step:
   - Simple: `PIL.Image.resize(target_size, PIL.Image.LANCZOS)`
   - Better: Run through Real-ESRGAN (`realesrgan-ncnn-vulkan`) for AI upscale
   - Result will be blurry but recognisable at HD

4. Load as textures in `p17_credits.py` replacing the text-only cards

**Code sketch:**
```python
from PIL import Image
# Install: pip install Pillow (or ilbmtoppm from netpbm)
# After decoding LBM to PNG:
img = Image.open("credits/psi.png").convert("RGBA")
img = img.resize((target_w, target_h), Image.LANCZOS)
```

**Note:** The original demo photos are from 1993 and are ~160×100 pixels in
320×200 Mode 13h at 256 colours.  Even with AI upscaling they will look
vintage/pixelated at 4K.  This may be desirable (authentic feel) or not
(depending on artistic direction).

---

### 2. Music Sync — Add libopenmpt for Row-Level Precision

**Current:** Timing table (seconds-based, approximate).
**Target:** Frame-perfect sync tied to S3M pattern/row position.

**Install:**
```bash
pip install python-openmpt
# or: pip install libopenmpt  (alternative binding)
# openmpt must be installed system-wide: apt install libopenmpt-dev
```

**Replace `demo/music.py` MusicPlayer entirely:**

```python
import openmpt
import pyaudio
import threading

class MusicPlayer:
    def __init__(self, music_dir):
        self._mod = None
        self._pa = pyaudio.PyAudio()
        self._stream = None
        self._playing = False
        self._lock = threading.Lock()
        # ... see libopenmpt Python docs for streaming callback setup

    def musrow(self):
        if self._mod:
            return self._mod.get_current_row()
        return 0

    def musplus(self):
        if not self._playing:
            return 0
        row = self._mod.get_current_row()
        pat = self._mod.get_current_pattern()
        # Map (pattern, row) pairs to cue values
        return self._cue_map.get((pat, row), -100)
```

This requires mapping specific `(pattern, row)` coordinates in MUSIC0.S3M and
MUSIC1.S3M to cue values.  Use a ScreamTracker 3 editor (OpenMPT, Schism
Tracker, or the original ST3) to identify the transition points.

---

### 3. Spaceship — Parse and Use Original .ASC Geometry

**Current:** Procedural box-grid city.
**Target:** Original city geometry from `original/VISU/C/` ASC files.

**The ASC files are at:** `original/VISU/` (look for `*.ASC`)

**The parser logic is in:** `original/VISU/C/MAIN.C` function `readasc()`

**ASC format (Autodesk Animator ASCII):**
```
Vertices: N
  x y z
  ...
Faces: M
  v1 v2 v3 [v4] colour_index
  ...
```

**Python ASC parser sketch:**
```python
def load_asc(path):
    vertices, faces = [], []
    with open(path) as f:
        # Parse "Vertices: N" block then "Faces: M" block
        # Return (np.array of vertices, list of (indices, colour))
    return vertices, faces
```

Also parse the `.VUE` camera animation files to replay the original flythrough
path rather than the sinusoidal approximation.

The `.MAT` material files define flat shading colours for each face — using
these would restore the exact visual palette of the original spaceship scene.

---

### 4. Implement the Original Bitmap Font

**Current:** System fonts via `pygame.font.SysFont()`.  The exact font face
varies by platform and won't look like the original.

**Target:** The original Future Crew bitmap font from `CREDITS/MAIN.C`.

**What exists in the original:**
`original/CREDITS/MAIN.C` contains `font[FONAY][1500]` — a 48-character
bitmap at 32px tall, stored as raw byte arrays.  Characters: A-Z, 0-9, space,
plus some symbols.  48 chars × ~32×32 = about 1500 bytes per row.

**Steps:**
1. Locate and decode the font data from `original/CREDITS/FONA.LBM` (likely)
   or embedded in `MAIN.C` as a byte array
2. Render it as a bitmap font atlas (one PNG with all characters)
3. In `utils/font.py` add a `BitmapFont` class that slices characters from
   the atlas and blits them at any scale

This makes the opening credits, end scroller, and credits text all look
authentic.

---

## Tier 2: Significant Visual Improvement

### 5. Explosion — Decode and Replay Original FLI Animation

**Current:** Generic particle system.
**Target:** Upscaled version of the original FLI animation frames.

**The FLI file is at:** `original/PAM/ANIM.FLI`

**FLI format:**
- Standard Autodesk FLI/FLC format (well-documented)
- Python: `pip install pillow` — Pillow can open `.fli` and `.flc` files
  via `PIL.Image.open("ANIM.FLI")` with `seek()` for each frame

**Steps:**
```python
from PIL import Image
img = Image.open("original/PAM/ANIM.FLI")
frames = []
try:
    while True:
        frames.append(img.copy().convert("RGBA"))
        img.seek(img.tell() + 1)
except EOFError:
    pass
# frames is now a list of PIL Images
# Upscale each: img.resize((target_w, target_h), Image.NEAREST) for pixel-art feel
# Or: Image.LANCZOS for smooth upscale
```

Load as a texture array or upload each frame as needed.  The original ran at
~10-15fps — replay at that rate in `p03_explosion.py`.

---

### 6. Cityscape — Procedural Improvements Without .ASC

Even without the original .ASC files, the procedural city in `p02_spaceship.py`
can be dramatically improved:

**Window lights:**
```python
# Add to box rendering: randomly lit windows as emissive quads
for each building:
    for each floor:
        for each window_position:
            if random() > 0.4:  # 60% of windows lit
                draw emissive yellow quad at window position
```

**Building variety:**
- Add setbacks (narrower top floors)
- Add antenna/spires on tall buildings
- Add a few dome/sphere shapes
- Vary width proportions more aggressively

**Roads and ground:**
- Dark grid of roads between buildings (current code leaves gaps — use them)
- Occasional street lights (bright point sprites at ground level)
- Faint vehicle lights moving along roads

**Atmosphere:**
- Ground-level fog (thick, blue-black)
- Building top lights blinking (aviation warning lights, red, slow blink)
- Neon glow on close buildings (bloom post-process)

**Camera path:**
Currently sinusoidal.  A more interesting path:
- Start very high (aerial overview)
- Descend toward street level through canyons between buildings
- Pull up at the end before transition

---

### 7. Voxel Landscape — Heightmap and Texturing

**Current:** Procedural layered-sine heightmap, height-based colour only.

**Improvements:**

**Heightmap quality:**
Replace the sine-sum with proper Perlin or simplex noise:
```python
# pip install noise
from noise import pnoise2
height = pnoise2(x * 0.01, z * 0.01, octaves=6, persistence=0.5)
```

Or generate a heightmap texture offline (using GIMP, Blender, or a terrain tool)
and sample it in the shader:
```glsl
uniform sampler2D uHeightmap;
float h = texture(uHeightmap, pos.xz / mapSize).r * maxHeight;
```

**Terrain texturing:**
```glsl
// In voxel.frag, replace the height-based colour with texture blending:
float grass  = smoothstep(40.0, 60.0, height);
float rock   = smoothstep(70.0, 90.0, height);
float snow   = smoothstep(130.0, 160.0, height);
vec3 col = mix(grassTex, rockTex, grass) ...
```

**Water in valleys:**
```glsl
if (height < waterLevel) {
    // Flat water surface
    vec3 waterNorm = vec3(sin(pos.x*0.1+time)*0.05, 1.0, cos(pos.z*0.1+time)*0.05);
    col = reflect(skyColour(waterNorm), waterNorm) * 0.8 + vec3(0.02, 0.05, 0.15);
}
```

**Shadows (basic):**
Cast a secondary ray toward the sun to determine if a terrain point is in
shadow.  This is expensive but gives dramatic results for mountain terrain.

---

### 8. Glenz — True XOR Palette Matching

**Current:** Additive blending (approximate).
**Target:** Integer palette-index XOR producing exact original colours.

**Architecture change needed:**

1. Define the original Glenz palette (extract from `original/GLENZ/` LBM or
   reverse-engineer from screenshots)
2. Render face IDs (not colours) to an integer texture
3. In a compositing shader, XOR face IDs and look up the result in the palette

```glsl
// Render each face to integer framebuffer
// layout(location=0) out int faceID;
// faceID = gl_PrimitiveID % 8;

// Compositing pass:
int id0 = texture(faceIDTex, uv).r;
int combined = id0 ^ previousID;  // XOR
vec3 col = palette[combined];
```

This requires `GL_INT` framebuffer attachments and careful face ID management.
It's the most technically involved improvement but would make the Glenz effect
look exactly like the original.

---

### 9. Forest Scroll — Parallax Texture Layers

**Current:** Procedural GLSL mountain silhouettes.

**Better approach:** Pre-render three 8K-wide PNG strips in Photoshop/GIMP:
- `forest_far.png`: distant mountains (3-4 shades of blue-grey)
- `forest_mid.png`: mid-range pine silhouettes (dark blue-green)
- `forest_near.png`: foreground pine tree silhouettes (black/very dark)

Scroll them at different rates as texture offsets in the shader.  This matches
the original approach (a wide LBM bitmap scrolling at fixed speed) but at HD.

The original Finnish forest scene had a specific colour palette: very dark
navy-black for near trees, deep blue for mountains, moonlit silver highlights.

---

## Tier 3: Polish and Correctness

### 10. Plasma — Restore Interlaced Fields

See Implementation Notes §10.  Add the `uK1..uK4` odd-field parameters.
This adds the characteristic shimmer that makes the plasma feel alive rather
than static.

**Required changes:**
- `plasma.frag`: branch on `int(vUV.y * uResY) % 2`
- `p11_plasma.py`: add `k1..k4` parameters tracking separately from `l1..l4`
- Add 4 more uniforms: `uK1, uK2, uK3, uK4`

---

### 11. Lens Path — Extract from Binary

The `pathdata1` and `pathdata2` arrays in `LENS/MAIN.C` can be extracted
from the LENS.EXE binary using the DOOBJ tool's inverse operation.

**Alternative:** Run the original LENS.C physics with `#define SAVEPATH`
in a DOS emulator (DOSBox), capture the output file, convert to Python list.

This would make the lens bounce path match the original exactly and sync
with the music as intended.

---

### 12. Mirror Ball — Proper Faceted Geometry

**Current:** GLSL sphere with floor() on the normal to simulate facets.
**Better:** Actual icosphere mesh with 162 flat reflective quad patches,
each rotated slightly differently.

The original mirror-ball effect worked by rendering many small square "mirrors"
each pointing in slightly different directions.  The GLSL `floor(normal *
facetScale)` trick approximates this but produces square screen-space artefacts
rather than proper facet geometry.

---

### 13. Add Transition Effects Between Parts

**Original:** Some parts faded in/out or had specific entry transitions.
The `screenin()` function in `CREDITS/MAIN.C` did a split-screen zoom.

**HD improvement:** Add an optional crossfade between parts by:
1. Rendering the outgoing part to an FBO for its last N frames
2. Rendering the incoming part to a second FBO for its first N frames
3. Blending between them in a compositing pass

The `Runner` class could manage this transparently.

---

### 14. Bloom Post-Processing Pass

Many of the effects (glenz vectors, star fields, explosion) would benefit from
a simple bloom pass — blurring bright pixels and adding them back.

**Standard bloom pipeline:**
1. Render scene to FBO
2. Threshold pass: keep only pixels above brightness 0.8
3. Gaussian blur the threshold result (2-pass: horizontal + vertical)
4. Add blurred result to original

This is entirely post-process and doesn't require changing any part code.
The bloom intensity can be tuned per-part via a `runner.set_bloom(strength)`
call.

---

### 15. Add the DDSTARS Hidden Part

`DDSTARS.EXE` was a secret part triggered by a specific key sequence during
the demo.  It showed a "Desert Dream"-style stars effect (scrolling star field
with specific colour cycling).

It could be added as:
- A part in the main sequence (breaking the "secret" nature)
- A key-triggered overlay: pressing `D` during any part shows it briefly
- An extra mode: `SECOND_REALITY_SHOW_DDSTARS=1` environment variable

---

## Asset Creation Summary

If creating assets from scratch (as intended — "redrawn at full HD"):

| Asset | Format | Dimensions | Tool |
|-------|--------|------------|------|
| Cityscape geometry | OBJ/GLTF | N/A (3D) | Blender |
| Forest panorama layers | PNG × 3 | 16384×2160 | GIMP/Photoshop |
| Voxel heightmap | PNG greyscale | 1024×1024 | Blender terrain |
| Terrain textures (grass, rock, snow) | PNG | 512×512 tileable | Any |
| Future Crew logo | SVG/PNG | 3840×1080 | Inkscape |
| Bitmap font atlas | PNG | 48×(char_w × char_h) | GIMP |
| Mirror ball environment map | HDR equirect | 4096×2048 | Blender HDRI |
| Credits portraits | PNG | 1920×1080 per | Illustrator/photo |

All assets go in `Python/assets/` following the naming convention in
`Python/assets/README.md`.

---

## Recommended Order of Work

1. **Fix voxel performance** (critical, blocks testing)
2. **Add libopenmpt music sync** (highest fidelity impact)
3. **Decode credits LBM photos** (highest emotional impact, easy)
4. **Parse .ASC spaceship geometry** (biggest visual improvement)
5. **Decode FLI explosion** (medium effort, good authenticity gain)
6. **Implement bitmap font** (low effort, touches every text element)
7. **Improve city procedurally** (while .ASC parser is in progress)
8. **Plasma interlaced fields** (easy, authentic shimmer)
9. **Bloom post-process** (easy, improves everything at once)
10. **Lens path extraction** (low priority, nice-to-have accuracy)
