#version 330 core

// Plasma effect — HD port of original/PLZPART/PLZ.C
//
// Original formula (from PLZ.C line 15):
//   PLZSINI(p1,p2,p3,p4) =
//     psini[x*32 + lsini[y*2+p2]*16 + p1] +
//     psini[y*4  + lsini[x*64+p4]*4  + p3]
//
// In GLSL we replace the integer lookup tables with continuous sin() calls.
// The four animation parameters (p1..p4) are animated over time and passed
// as uniforms, matching the interlaced even/odd field structure of the original.

in vec2 vUV;
out vec4 fragColour;

uniform float uTime;      // seconds elapsed in this part
uniform float uP1;        // even-field param 1 (l1 in original)
uniform float uP2;        // even-field param 2 (l2)
uniform float uP3;        // even-field param 3 (l3)
uniform float uP4;        // even-field param 4 (l4)
uniform int   uPalIndex;  // 0..5, selects colour palette

// Map a normalised plasma value [-2..2] to a colour.
// Six palettes matching pals[6] from PLZ.C (approximated with GLSL math).
vec3 applyPalette(float v, int pal) {
    float t = v * 0.25 + 0.5;          // remap to [0..1]
    t = clamp(t, 0.0, 1.0);

    if (pal == 0) {
        // Blue-cyan
        return vec3(0.0, t * 0.6, t);
    } else if (pal == 1) {
        // Red-orange fire
        return vec3(t, t * t * 0.6, 0.0);
    } else if (pal == 2) {
        // Green
        return vec3(0.0, t, t * 0.4);
    } else if (pal == 3) {
        // Purple-magenta
        return vec3(t * 0.8, 0.0, t);
    } else if (pal == 4) {
        // Yellow-white
        return vec3(t, t * 0.9, t * 0.4);
    } else {
        // Rainbow (pal 5)
        float h = fract(t + 0.0);
        // Quick HSV→RGB
        vec3 c = clamp(abs(mod(h * 6.0 + vec3(0.0, 4.0, 2.0), 6.0) - 3.0) - 1.0,
                       0.0, 1.0);
        return c * t;
    }
}

// Core plasma formula.
// x, y: normalised screen coords (scaled to match original 320×200 grid)
float plasma(float x, float y, float p1, float p2, float p3, float p4) {
    // Scale to original coordinate space for character-faithful reproduction
    float sx = x * 160.0;  // 0..320
    float sy = y * 100.0;  // 0..200

    // Mimic lsini[] (secondary modulation table)
    float lx = sin(sx * 0.031416 + p4 * 0.001);   // lsini[x*64+p4]
    float ly = sin(sy * 0.062832 + p2 * 0.001);   // lsini[y*2+p2]

    // Primary plasma sums — two layers (mimic psini even + odd interlace)
    float a = sin(sx * 0.019635 + ly * 16.0 * 0.019635 + p1 * 0.001);
    float b = sin(sy * 0.004909 + lx * 4.0  * 0.004909 + p3 * 0.001);

    return a + b;
}

void main() {
    float v = plasma(vUV.x, vUV.y, uP1, uP2, uP3, uP4);
    vec3 col = applyPalette(v, uPalIndex);
    fragColour = vec4(col, 1.0);
}
