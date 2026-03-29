#version 330 core

// Mountain/forest parallax scroll (MNTSCRL.EXE)
// Procedural night-scene with 3 mountain silhouette layers

in vec2 vUV;
out vec4 fragColour;

uniform float uTime;
uniform float uScroll;   // horizontal scroll (0..1 range, wraps)
uniform float uAspect;

// Mountain profile: returns height at a given x for a given layer
float mountain(float x, float seed, float roughness) {
    float h = 0.0;
    h += sin(x * 1.5  + seed) * 0.15;
    h += sin(x * 3.7  + seed * 1.3) * 0.08;
    h += sin(x * 7.1  + seed * 0.7) * 0.04;
    h += sin(x * 13.3 + seed * 2.1) * 0.02 * roughness;
    h += sin(x * 27.0 + seed * 0.4) * 0.01 * roughness;
    return h + 0.32;
}

// Star field
float stars(vec2 uv, float scale) {
    vec2 cell = floor(uv * scale);
    vec2 frac = fract(uv * scale);
    float h = fract(sin(dot(cell, vec2(127.1, 311.7))) * 43758.5453);
    float brightness = step(0.97, h);
    float d = length(frac - 0.5);
    return brightness * smoothstep(0.25, 0.0, d);
}

void main() {
    vec2 uv = vUV;

    // Sky gradient: deep blue-black at bottom, slightly lighter at top
    vec3 sky = mix(vec3(0.0, 0.01, 0.08), vec3(0.02, 0.04, 0.15),
                   smoothstep(0.3, 1.0, uv.y));

    // Moon
    vec2 moonPos = vec2(0.75, 0.78);
    float moonDist = length(uv - moonPos);
    float moon = smoothstep(0.05, 0.04, moonDist);
    float glow = exp(-moonDist * 8.0) * 0.3;
    sky += vec3(0.9, 0.85, 0.7) * moon + vec3(0.5, 0.45, 0.3) * glow;

    // Stars (parallax: stars scroll very slowly)
    float starScroll = uScroll * 0.05;
    sky += vec3(0.9, 0.9, 1.0) * stars(uv + vec2(starScroll, 0.0), 80.0) * 1.5;
    sky += vec3(0.8, 0.8, 1.0) * stars(uv + vec2(starScroll * 0.7, 0.0), 50.0);

    vec3 col = sky;

    // Layer 3 (far mountains, scroll slowest)
    float x3 = uv.x * uAspect * 1.5 + uScroll * 0.3;
    float h3 = mountain(x3, 1.23, 0.5);
    float moonlight3 = 0.06 + max(0.0, (moon + glow * 0.5) * 0.08);
    if (uv.y < h3) {
        col = mix(vec3(0.03, 0.04, 0.08), col, smoothstep(h3 - 0.005, h3, uv.y));
        col = vec3(0.04, 0.05, 0.12) * moonlight3 * 3.0;
    }

    // Layer 2 (mid mountains)
    float x2 = uv.x * uAspect * 1.5 + uScroll * 0.6;
    float h2 = mountain(x2, 4.56, 0.8) - 0.05;
    if (uv.y < h2) {
        col = vec3(0.02, 0.03, 0.07);
        // Moonlit ridge
        float ridge = smoothstep(h2 - 0.008, h2, uv.y);
        col += vec3(0.1, 0.09, 0.07) * ridge * (moon + glow);
    }

    // Layer 1 (near trees / forest, scroll fastest)
    float x1 = uv.x * uAspect * 2.0 + uScroll * 1.0;
    // Trees: jagged silhouette
    float treeH = 0.15 + sin(x1 * 8.0) * 0.02 + sin(x1 * 17.0) * 0.01;
    treeH += step(0.5, fract(x1 * 2.0)) * 0.04;  // tree tops
    if (uv.y < treeH) {
        col = vec3(0.0, 0.0, 0.0);
        // Moonlit tips
        float tip = smoothstep(treeH - 0.01, treeH, uv.y);
        col += vec3(0.06, 0.055, 0.04) * tip * (moon * 2.0 + glow);
    }

    fragColour = vec4(col, 1.0);
}
