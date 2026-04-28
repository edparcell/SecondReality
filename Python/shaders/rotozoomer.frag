#version 330 core

// Rotozoomer — HD port of the second sub-effect in original/LENS/MAIN.C
//
// Classic demo technique: apply a rotation+scale matrix to UV coords before
// sampling a tiled texture, creating infinite zoom+rotation.
//
// The original used a pre-recorded path (pathdata2[]) for the zoom/rotation
// animation.  We animate with time-driven sinusoidal motion.

in vec2 vUV;
out vec4 fragColour;

uniform sampler2D uTile;     // tiled texture (procedural checkerboard if not bound)
uniform float uAngle;        // rotation angle in radians
uniform float uZoom;         // zoom factor (>1 = zoom in)
uniform vec2  uOffset;       // UV translation offset [0..1]
uniform float uTime;

// Generate a procedural checkerboard if no texture is available
vec3 checkerboard(vec2 uv) {
    float scale = 8.0;
    vec2 tile = floor(uv * scale);
    float check = mod(tile.x + tile.y, 2.0);
    vec3 colA = vec3(0.9, 0.7, 0.1);  // gold
    vec3 colB = vec3(0.1, 0.05, 0.3); // dark purple
    return mix(colB, colA, check);
}

void main() {
    // Centre UV at (0.5, 0.5)
    vec2 uv = vUV - 0.5;

    // Apply rotation matrix
    float c = cos(uAngle);
    float s = sin(uAngle);
    uv = vec2(c * uv.x - s * uv.y,
              s * uv.x + c * uv.y);

    // Apply zoom (scale)
    uv /= max(uZoom, 0.01);

    // Re-centre and add translation offset
    uv += 0.5 + uOffset;

    // Sample with tiling (fract wraps naturally)
    vec3 col = checkerboard(fract(uv));

    fragColour = vec4(col, 1.0);
}
