#version 330 core

// Lens distortion — HD port of the lens effect from original/LENS/MAIN.C
//
// The original pre-computed a displacement table mapping each output pixel to
// a source pixel via a spherical lens formula.  We compute this per-pixel in
// the shader at full 4K resolution.
//
// Chromatic aberration: the original rendered 4 colour layers at slightly
// different radii.  We sample R, G, B at three different radii to reproduce
// this effect.

in vec2 vUV;
out vec4 fragColour;

uniform sampler2D uSource;    // source texture (procedural background or prev frame)
uniform vec2  uLensPos;       // normalised lens centre position [0..1]
uniform float uLensStrength;  // distortion strength (0=none, 1=heavy)
uniform float uLensRadius;    // normalised radius of lens effect [0..1]
uniform float uChromaOffset;  // chromatic aberration spread (try 0.003)
uniform float uTime;

// Barrel/spherical lens distortion
vec2 lensDistort(vec2 uv, vec2 centre, float strength, float radius) {
    vec2 delta = uv - centre;
    float dist = length(delta);
    if (dist > radius) return uv;

    // Spherical mapping: objects appear through a glass sphere
    float normalised = dist / radius;
    float bend = 1.0 - sqrt(1.0 - normalised * normalised) * strength;
    return centre + delta * bend;
}

void main() {
    // Three slightly different radii for chromatic aberration
    float rr = uLensRadius + uChromaOffset;
    float rg = uLensRadius;
    float rb = uLensRadius - uChromaOffset;

    vec2 uvR = lensDistort(vUV, uLensPos, uLensStrength, rr);
    vec2 uvG = lensDistort(vUV, uLensPos, uLensStrength, rg);
    vec2 uvB = lensDistort(vUV, uLensPos, uLensStrength, rb);

    float r = texture(uSource, uvR).r;
    float g = texture(uSource, uvG).g;
    float b = texture(uSource, uvB).b;

    fragColour = vec4(r, g, b, 1.0);
}
