# Technical Reference: VGA Programming Techniques

Key VGA programming techniques used throughout Second Reality, relevant for the Python/OpenGL HD recreation.

---

## Standard Mode 13h (320×200×256)

The most common mode in the demo:
- Linear framebuffer at segment `0xA000` (physical address `0xA0000`)
- 320 × 200 = 64,000 bytes
- 256-colour indexed palette (6-bit DAC: each R, G, B component 0–63)
- Set with BIOS `INT 10h, AX=0013h`
- Direct pixel write: `vram[y * 320 + x] = colour_index`

---

## Palette Management

```c
// Set palette entry #index to (r, g, b) — values 0–63
outp(0x3C8, index);   // write DAC address
outp(0x3C9, r);       // red (0-63)
outp(0x3C9, g);       // green (0-63)
outp(0x3C9, b);       // blue (0-63)

// Read palette entry
outp(0x3C7, index);   // read DAC address
r = inp(0x3C9);
g = inp(0x3C9);
b = inp(0x3C9);

// Upload full 768-byte palette (256 × 3)
outp(0x3C8, 0);
for (i = 0; i < 768; i++) outp(0x3C9, palette[i]);
```

**Critical:** Palette updates during active display cause "snow" (colour glitches). Do palette uploads during vertical blank only.

---

## Vertical Blank Synchronisation

```c
// Wait for vertical blank:
while (!(inp(0x3DA) & 8));   // wait for VBlank start (bit 3)
while ((inp(0x3DA) & 8));    // wait for VBlank end (optional — just needs start)

// OR: wait for display active period:
while (inp(0x3DA) & 8);     // wait for VBlank to end first
while (!(inp(0x3DA) & 8));  // then wait for next VBlank
```

Port `0x3DA` (Input Status Register 1):
- Bit 0: Horizontal retrace in progress
- Bit 3: Vertical retrace in progress

---

## CRTC Registers (via port 0x3D4/0x3D5)

The Cathode Ray Tube Controller governs timing and display position:

```c
// Display start address (which byte of VRAM to start displaying)
// Allows hardware scrolling without data movement
outp(0x3D4, 0x0C); outp(0x3D5, high_byte);  // high 8 bits
outp(0x3D4, 0x0D); outp(0x3D5, low_byte);   // low 8 bits
// Full 16-bit offset: displayed = VRAM[start_address]

// Split screen Y position (where the second virtual screen starts)
outp(0x3D4, 0x18); outp(0x3D5, split_y & 0xFF);
// Also bits in registers 0x07 and 0x09

// Screen width (bytes per row / 2)
outp(0x3D4, 0x13); outp(0x3D5, bytes_per_row / 2);
// Default: 40 (for 320px mode = 320/8 = 40... actually 320/2 = 160? No: 320 bytes / 2 = 160? )
// For mode 13h: 40 (320 bytes per row = 40 × 8 bit planes... wait, mode 13h is linear)
// Actually in mode 13h: 80 bytes per CRTC "character" (320 / 4 = 80)
```

### Horizontal Smooth Scrolling (Fine Scroll)

The Attribute Controller (port 0x3C0) register 0x13 controls fine horizontal scroll:
```c
// Access attribute controller:
inp(0x3DA);        // reset flip-flop to address mode
outp(0x3C0, 0x13); // select register 0x13
outp(0x3C0, value); // pixel pan: 0–3 (pixels to shift left)
outp(0x3C0, 0x20); // re-enable display
```

This shifts the display left by 0–3 pixels without moving data, allowing sub-byte smooth scrolling.

---

## Mode X (Planar 320×240/320×200)

Mode X uses the VGA's 4 memory planes in a 256-colour mode:
- Each plane holds 1/4 of the pixels (pixels 0, 4, 8... on plane 0; 1, 5, 9... on plane 1; etc.)
- More complex to write to, but allows 4× more addressable VRAM and faster block operations

```c
// Write to specific plane(s):
outp(0x3C4, 0x02);         // Sequencer register 2: plane mask
outp(0x3C5, plane_mask);   // 0x01=plane0, 0x02=plane1, 0x04=plane2, 0x08=plane3, 0x0F=all

// Read from specific plane:
outp(0x3CE, 0x04);         // GDC register 4: read map select
outp(0x3CF, plane_number); // 0-3

// Double buffer in Mode X (two 320×200 pages):
// Page 0: offset 0
// Page 1: offset 0x4B00 (19200) for 320×240, or 0x4E20 (20000) for 320×200
```

---

## Tweaked VGA Modes

Second Reality uses extensively tweaked CRTC settings for non-standard resolutions. Key tweaks:

### 320×400 (Double-height)

```c
// Halve the pixel clock by disabling line doubling:
outp(0x3D4, 0x09);  // max scan line register
outp(0x3D5, 0x00);  // line doubling off (normally 0x41 for 200-line mode)
// This makes each scanline 1 physical pixel tall instead of 2
// Result: 400 scanlines displayed instead of 200
```

### Split Screen for Widescreen Effect

The ALKU opening credits use split screen to create letterbox bars:
```c
// Display first N lines from one area, remaining lines from offset 0
// This creates an "upper" and "lower" framebuffer region
outp(0x3D4, 0x18); outp(0x3D5, split_y);
```

---

## EGA Mode (16 colours)

EGA mode 10h: 640×350×16 colours, used in Techno part:
- 4 bitplanes, each contributing 1 bit to the 4-bit colour index per pixel
- Write to planes via Sequencer register 2
- Read planes via GDC register 4
- Each byte written covers 8 pixels (1 bit each)

EGA palette: maps 4-bit index (0–15) to 6-bit RGB (EGA native) via the Attribute Controller palette registers (AC registers 0–15).

---

## Double Buffering

Standard double-buffer pattern in Mode 13h:
```c
// Draw to back buffer (hidden area of VRAM):
char *backbuf = vram + 64000;  // or allocated in higher VRAM

// Wait for VBlank, then switch display:
while (!(inp(0x3DA) & 8));
outp(0x3D4, 0x0C); outp(0x3D5, 0xF8);  // display from offset 64000 >> 1
outp(0x3D4, 0x0D); outp(0x3D5, 0x00);

// Now draw to the other buffer...
```

The TWIST part uses this technique explicitly:
```c
vram1 = 0xA000:0x0000;  // page 0
vram2 = 0xA000:0x8000;  // page 1 (at byte offset 32768)
// Alternate display start: 0x0000 / 0x8000 (paragraphs 0 / 128)
```

---

## Relevance for Python/OpenGL Recreation

In the HD Python version, these concepts map as follows:

| DOS VGA concept | Python/OpenGL equivalent |
|---|---|
| Mode 13h 320×200 | OpenGL viewport, 320×200 render texture upscaled |
| Palette (256-colour indexed) | GLSL uniform array, colour lookup texture |
| VBlank sync | `pygame.display.flip()` / VSync enabled |
| CRTC start address scroll | UV offset on fullscreen quad |
| Split screen | Render to two textures, composite with scissor/stencil |
| EGA planes | Multiple framebuffers / blending modes |
| Copper (VBlank callback) | Per-frame Python callback before display |
| Sine table `sin1024[]` | `math.sin()` / numpy vectorised sin |
| Fixed-point 16.16 math | Python floats (or numpy float32) |
| Mode X double buffer | OpenGL double buffering (default) |

The effects themselves:
- **Plasma:** Compute `f(x, y, t)` as sum-of-sines, write to texture, render as fullscreen quad
- **Lens:** Precompute displacement map texture, use GLSL to sample `texture(src, uv + displacement)`
- **Rotozoomer:** 2D rotation/scale matrix in GLSL, sample tiling background texture
- **Glenz vectors:** Standard 3D rendering with additive blending and custom palette
- **Voxel landscape:** Height field computed per-column in vertex/fragment shader
- **Dot tunnel:** Particle system with depth sorting
