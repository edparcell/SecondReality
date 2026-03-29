#version 330 core

// Background for the lens part: animated plasma-like texture
// (replaces the original .LBM background image)

in vec2 vUV;
out vec4 fragColour;

uniform float uTime;

void main() {
    float x = vUV.x * 6.28318;
    float y = vUV.y * 6.28318;

    float v = sin(x * 2.0 + uTime) * 0.5
            + sin(y * 1.5 + uTime * 0.7) * 0.3
            + sin((x + y) * 1.2 + uTime * 0.5) * 0.2;
    v = v * 0.5 + 0.5;

    // Rich colour mapping
    vec3 col;
    col.r = sin(v * 3.14159 + uTime * 0.3) * 0.5 + 0.5;
    col.g = sin(v * 3.14159 + 2.094 + uTime * 0.2) * 0.5 + 0.5;
    col.b = sin(v * 3.14159 + 4.189 + uTime * 0.4) * 0.5 + 0.5;

    fragColour = vec4(col * 0.8, 1.0);
}
