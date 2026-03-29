#version 330 core

// Voxel landscape — HD port of the Comanche-style column-raycaster
// from original/COMAN/MAIN.C and HARD/MAIN.C.
//
// Original algorithm (per screen column):
//   1. Cast a ray from camera position in the viewing direction
//   2. Sample the heightmap at each step along the ray
//   3. If height > projected_height, draw a vertical column of pixels
//
// In the fragment shader we implement this as a per-pixel ray march,
// which maps directly to the original column-loop concept but runs on
// the GPU for every pixel at 4K.

in vec2 vUV;
out vec4 fragColour;

uniform vec3  uCamPos;       // camera position (x, z, height)
uniform float uCamAngle;     // camera yaw in radians
uniform float uCamPitch;     // camera pitch (0 = horizontal)
uniform float uTime;
uniform vec2  uResolution;   // render resolution (e.g. 3840, 2160)

// Heightmap: procedurally generated from layered sines
// (replaces the original HARD.LBM / terrain data)
float heightmap(vec2 pos) {
    float h = 0.0;
    // Layer 1: large hills
    h += sin(pos.x * 0.03) * cos(pos.y * 0.025) * 80.0;
    // Layer 2: medium ridges
    h += sin(pos.x * 0.07 + 1.3) * sin(pos.y * 0.08) * 40.0;
    // Layer 3: small detail
    h += sin(pos.x * 0.2 + pos.y * 0.15) * 15.0;
    // Layer 4: noise-like micro detail
    h += sin(pos.x * 0.5) * cos(pos.y * 0.4) * 6.0;
    return h + 50.0;  // base height offset
}

// Colour from height (terrain + sky gradient)
vec3 terrainColour(float height, float distance) {
    // Height-based terrain colouring
    vec3 col;
    if (height < 30.0) {
        col = vec3(0.05, 0.2, 0.05);  // dark green valley
    } else if (height < 80.0) {
        float t = (height - 30.0) / 50.0;
        col = mix(vec3(0.1, 0.35, 0.1), vec3(0.5, 0.4, 0.25), t);
    } else {
        float t = clamp((height - 80.0) / 80.0, 0.0, 1.0);
        col = mix(vec3(0.5, 0.4, 0.25), vec3(0.95, 0.95, 0.95), t);
    }
    // Distance fog
    float fog = exp(-distance * 0.001);
    vec3 fogColour = vec3(0.4, 0.55, 0.75);
    return mix(fogColour, col, fog);
}

vec3 skyColour(float v) {
    // v: 0 = horizon, 1 = zenith
    return mix(vec3(0.5, 0.65, 0.85), vec3(0.05, 0.1, 0.3), v);
}

void main() {
    vec2 uv = vUV * 2.0 - 1.0;  // NDC [-1, 1]
    uv.x *= uResolution.x / uResolution.y;

    // Camera setup
    float c = cos(uCamAngle);
    float s = sin(uCamAngle);

    // Ray direction in world XZ plane
    vec2 rayDir2D = vec2(c + uv.x * 0.8, s + uv.x * 0.8 * (s/max(abs(c),0.001)));
    rayDir2D = normalize(vec2(c - s * uv.x, s + c * uv.x));

    // Vertical FOV / pitch
    float horizonY = 0.5 + uCamPitch * 0.3;

    // Column raycast
    float maxDist   = 800.0;
    float stepSize  = 1.5;
    float maxHeight = -1e9;
    vec3  hitColour = skyColour(clamp((vUV.y - horizonY) / (1.0 - horizonY), 0.0, 1.0));
    bool  hit       = false;

    vec2 pos = uCamPos.xz;
    float camHeight = uCamPos.y + 120.0;

    for (float d = 1.0; d < maxDist; d += stepSize) {
        vec2 p = pos + rayDir2D * d;
        float terrH = heightmap(p);

        // Project to screen: how many pixels tall does this terrain column appear?
        float projH = (camHeight - terrH) / d * 200.0;
        float screenY = horizonY - projH / uResolution.y;

        if (screenY < vUV.y && screenY > maxHeight - 0.5) {
            maxHeight = screenY;
            hitColour = terrainColour(terrH, d);
            hit = true;
            stepSize = 1.5 + d * 0.005;  // adaptive step: coarser at distance
        }

        if (d > 200.0) stepSize = 3.0;
        if (d > 400.0) stepSize = 6.0;
    }

    fragColour = vec4(hitColour, 1.0);
}
