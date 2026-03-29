#version 330 core

// Jelly picture phases 2+3: horizontal slide-in and ripple

in vec2 vUV;
out vec4 fragColour;

uniform float uTime;
uniform float uXOffset;  // 0=fully revealed, 1=fully off-screen right
uniform float uRipple;   // horizontal ripple amplitude

// Procedural "picture": abstract coloured image (replacement for JP.LBM)
vec3 picture(vec2 uv) {
    // Colourful abstract pattern with geometric shapes
    vec3 col = vec3(0.0);

    // Background gradient
    col = mix(vec3(0.05, 0.02, 0.15), vec3(0.15, 0.05, 0.3),
              length(uv - 0.5));

    // Concentric rings
    float d = length(uv - 0.5) * 6.0;
    float ring = abs(fract(d) - 0.5) * 2.0;
    col += vec3(0.0, 0.2, 0.5) * (1.0 - ring) * 0.4;

    // Diagonal stripes
    float stripe = abs(fract((uv.x + uv.y) * 8.0) - 0.5) * 2.0;
    col += vec3(0.3, 0.1, 0.0) * (1.0 - stripe) * 0.3;

    // Radial "logo" circle in the centre
    float centre = length(uv - 0.5);
    col += vec3(0.8, 0.6, 0.1) * smoothstep(0.18, 0.15, centre);
    col += vec3(1.0, 0.9, 0.3) * smoothstep(0.06, 0.04, centre);

    return clamp(col, 0.0, 1.0);
}

void main() {
    // Apply horizontal ripple (phase 3)
    float rippleOffset = uRipple * sin(vUV.y * 20.0 + uTime * 5.0) * 0.05;

    // Apply slide offset (phase 2): picture slides in from right
    float px = vUV.x - uXOffset + rippleOffset;

    if (px < 0.0 || px > 1.0) {
        // Show interference pattern in the area not yet covered
        float bx = floor(vUV.x * 10.0 + uTime * 2.0);
        float by = floor(vUV.y * 8.0  - uTime * 1.5);
        int p = (int(bx) ^ int(by)) & 7;
        vec3 pal[8];
        pal[0] = vec3(0.0,0.0,0.3); pal[1] = vec3(0.0,0.3,0.3);
        pal[2] = vec3(0.3,0.0,0.3); pal[3] = vec3(0.3,0.3,0.0);
        pal[4] = vec3(0.0,0.0,0.6); pal[5] = vec3(0.0,0.6,0.0);
        pal[6] = vec3(0.6,0.0,0.0); pal[7] = vec3(0.3,0.3,0.3);
        fragColour = vec4(pal[p], 1.0);
    } else {
        fragColour = vec4(picture(vec2(px, vUV.y)), 1.0);
    }
}
