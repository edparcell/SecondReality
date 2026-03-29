#version 330 core

// Shared vertex shader for all fullscreen/2D quad effects.
// Input layout matches the VAO built in runner.py:
//   attrib 0: vec2 position  (NDC, -1..1)
//   attrib 1: vec2 uv        (0..1)

layout(location = 0) in vec2 aPos;
layout(location = 1) in vec2 aUV;

out vec2 vUV;

void main() {
    vUV = aUV;
    gl_Position = vec4(aPos, 0.0, 1.0);
}
