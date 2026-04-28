#version 330 core

// Jelly picture phase 1: EGA-style interference boxes (doit1/2/3 from JP.C)

in vec2 vUV;
out vec4 fragColour;

uniform float uTime;
uniform float uPhase;  // 0..1 progress through interference phase

void main() {
    // CRTC start address rotation creates scrolling interference bands
    float scroll = uTime * 3.0;

    // Three overlapping interference patterns (doit1, doit2, doit3)
    float b1 = floor((vUV.x + scroll * 0.3) * 8.0);
    float b2 = floor((vUV.y + scroll * 0.2) * 6.0);
    float b3 = floor((vUV.x * 1.5 - vUV.y + scroll * 0.4) * 5.0);

    // XOR of plane values
    int p = (int(b1) ^ int(b2) ^ int(b3)) & 15;

    // EGA colours
    vec3 cols[16];
    cols[0]  = vec3(0.0,   0.0,   0.0);
    cols[1]  = vec3(0.0,   0.0,   0.67);
    cols[2]  = vec3(0.0,   0.67,  0.0);
    cols[3]  = vec3(0.0,   0.67,  0.67);
    cols[4]  = vec3(0.67,  0.0,   0.0);
    cols[5]  = vec3(0.67,  0.0,   0.67);
    cols[6]  = vec3(0.67,  0.33,  0.0);
    cols[7]  = vec3(0.67,  0.67,  0.67);
    cols[8]  = vec3(0.33,  0.33,  0.33);
    cols[9]  = vec3(0.33,  0.33,  1.0);
    cols[10] = vec3(0.33,  1.0,   0.33);
    cols[11] = vec3(0.33,  1.0,   1.0);
    cols[12] = vec3(1.0,   0.33,  0.33);
    cols[13] = vec3(1.0,   0.33,  1.0);
    cols[14] = vec3(1.0,   1.0,   0.33);
    cols[15] = vec3(1.0,   1.0,   1.0);

    fragColour = vec4(cols[p], 1.0);
}
