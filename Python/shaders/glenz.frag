#version 330 core

// Glenz vector fragment shader.
//
// The original used XOR palette tricks to produce semi-transparent faces —
// overlapping faces combined their palette indices with XOR, yielding lighter
// colours and a glassy appearance.
//
// In OpenGL we replicate this with additive blending (GL_ONE, GL_ONE) for
// the "glow" contribution, or screen blending for a softer look.
// Each face is drawn with a base colour; the shader adds rim lighting and
// a specular highlight to give the HD metallic/glassy feel.

in vec3 vNormal;
in vec3 vWorldPos;
out vec4 fragColour;

uniform vec3  uBaseColour;    // face base colour
uniform vec3  uLightDir;      // normalised light direction (world space)
uniform float uAlpha;         // face transparency (0=invisible, 1=opaque)
uniform float uTime;

void main() {
    vec3 N = normalize(vNormal);
    vec3 L = normalize(uLightDir);

    // Diffuse
    float diff = max(dot(N, L), 0.0);

    // Specular (Blinn-Phong)
    vec3 viewDir = normalize(vec3(0.0, 0.0, 1.0) - vWorldPos);
    vec3 H = normalize(L + viewDir);
    float spec = pow(max(dot(N, H), 0.0), 64.0);

    // Rim light (glenz glow at silhouette edges)
    float rim = 1.0 - abs(dot(N, viewDir));
    rim = pow(rim, 2.0) * 0.5;

    vec3 col = uBaseColour * (0.15 + diff * 0.7) + vec3(spec) + uBaseColour * rim;
    fragColour = vec4(col, uAlpha);
}
