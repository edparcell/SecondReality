# Part 02: Opening Credits II — Spaceship Flyby (U2A)

**Directory:** `original/VISU/`
**Output EXE:** `U2A.EXE`
**Coder:** PSI
**Pipeline tool directory:** `original/VISU/C/`

---

## Visual Effect

A massive 3D spaceship flies from behind the viewer toward the horizon at high speed, starting enormous and shrinking to a pixel. The ship has flat-shaded polygons with multiple colour bands. When it reaches pixel-size, it "explodes" in a Praxis-style ring blast (actually handled by the next part, PAM.EXE).

This is followed by a second vector scene (`U2E.EXE`) — the full space battle — using the same renderer.

---

## Technical Implementation

### Overview

This is the most architecturally complex part of the demo. It uses a full **3D rendering pipeline** with:
- A custom 3DS MAX → binary scene converter
- Runtime scene playback with animated camera
- Flat-shaded polygon rendering with Z-sort (painter's algorithm)
- Multiple objects, each with their own transformation matrix

### Source Structure

**Converter tool** (`original/VISU/C/`):

| File | Purpose |
|---|---|
| `MAIN.C` | Tool main: reads 3DS scene, converts to binary |
| `READASC.C` | Parses Autodesk Animator `.ASC` (ASCII scene export) |
| `READVUE.C` | Parses `.VUE` camera/animation files |
| `READMAT.C` | Parses material definitions |
| `READINF.C` | Parses `.INF` scene info file |
| `SAVE.C` | Outputs binary object/scene files (`.00M`, `.0AA`, `.00O`) |
| `OSORT.C` | Sorts faces by depth for painter's algorithm |
| `UTIL.C` | 3D math utilities |
| `CITY.C` | City-specific data handling |
| `CPLAY.C` | Scene playback |
| `U2A.C` / `U2AOLD.C` | Spaceship scene specific code |
| `U2E.C` / `U2EOLD.C` | Space battle scene specific code |
| `SRVEC.C` | Screen-space vector utilities |
| `OPT.C` | Optimisation passes |

**Runtime renderer** (`original/VISU/`):

| File | Purpose |
|---|---|
| `AMAIN.ASM` | Main animation/playback loop |
| `AVID.ASM` | Video output routines |
| `ADRAW.ASM` | Polygon drawing routines |
| `ADRAWCLP.ASM` | Clipped polygon drawing |
| `ADATA.ASM` | Embedded scene data |
| `ACALC.ASM` | 3D transform calculations |
| `AVIDFILL.ASM` | Polygon fill routines |
| `AVIDM1.ASM` / `AVIDM2.ASM` | Mode-specific video routines |
| `ATEXT.ASM` | Text rendering |
| `DOFILL.C` / `DOFILLT.C` | Polygon fill (C side) |
| `DOSIN.C` | Sine table generation |
| `DOTAN.C` | Tangent table generation |
| `VISU.C` / `VISUX.C` | Top-level scene controller |
| `KOE.ASM` | Test/experiment code |

### 3D Pipeline

```
3DS MAX scene
     ↓
Autodesk Animator .ASC export (text format: vertex/face lists)
     ↓
VISU/C/MAIN.C converter
     ↓
Binary .00M / .0AA / .00O files
     ↓
Embedded via INCBIN into U2A.EXE / U2E.EXE
     ↓
AMAIN.ASM playback + transform + AVID.ASM rasteriser
```

### Coordinate System

- World coordinates are stored as 32-bit integers (scaled by `scale` factor, default 100.0)
- Rotation matrices are 3×3 fixed-point (`rmatrix` type in `c.h`)
- Perspective projection: standard divide-by-Z
- Z-sort: `objectsort()` in `OSORT.C` sorts faces front-to-back per frame

### Polygon Fill (`VISU/C/MAIN.C:cfill`)

The fill routine `cfill()` uses a scan-line algorithm with fixed-point left/right edge interpolation:
- Input is a stream of edge update commands
- Each scan line: update `lx`, `rx` accumulators, fill span with solid colour
- Dual buffers: `fill_color[64000]` (colour) and `fill_object[64000]` (object ID per pixel)

### Camera Animation

Camera position/orientation is read from `.VUE` files (Autodesk Animator camera tracks). The `MIKKO.VUE` file in `original/3DS/` is the camera animation for the spaceship scene.

### 3DS Source Files (`original/3DS/`)

| File | Description |
|---|---|
| `UUSALKU.3DS` / `.ASC` / `.PRJ` | "New opening" spaceship model |
| `PXLSHIP.3DS` / `2` / `3` | Pixel's spaceship models (variants) |
| `PASKA2.3DS` | Rough geometry test ("paska" = Finnish for "shit") |
| `CITYBBK.3DS` | City background |
| `I_SHP_3.3DS` | Another ship variant |
| `MIKKO.VUE` | Camera animation |
| `CITY.ASC` | City scene ASCII export |
| `U2CITY2..11.PRJ` | City scene project files (11 variants) |
| `U2E.PRJ` | Space battle scene project |
| `PEILI.PRJ` / `PEILI2.PRJ` | Mirror ball projects |
| `ALKU2.PRJ` | Opening scene project |

---

## The City Flyby Scene

The `CITY.C` / `cityflag` in the converter handles a special city flyby mode where the camera flies through a 3D city. This appears to be an alternate scene (possibly used in `U2E.EXE` as a background).

The city uses a background bitmap (`CITY.LBM`, `CITYBBK.3DS`) blended with the 3D rendered objects.

---

## Surprising Details

- The converter tool outputs a `report` file during development with face/vertex counts per object
- `PASKA2.3DS` ("shit model") suggests rapid iteration on ship geometry
- The scene files have 11 city project variants (`U2CITY2` through `U2CITY11`), showing extensive iteration
- The `cfill` routine also writes to `fill_object[]` (tracking which object owns each pixel), presumably used for click detection or occlusion during the development tool phase
- Objects beginning with `_` (underscore) in their name are always pushed to the far background in Z-sorting (`co[a].dist = 100000000L`) — a clever hack for skybox/background objects
