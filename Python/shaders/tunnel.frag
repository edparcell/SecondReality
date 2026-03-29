#version 330 core

// Dot tunnel background shader.
// Renders the tunnel walls as a textured cylinder, used as the background
// behind the point-sprite dots in p06_dot_tunnel.py.

in vec2 vUV;
out vec4 fragColour;

uniform float uTime;
uniform float uScrollZ;  // tunnel z-scroll position

// Tunnel: barrel-mapped texture on a cylinder
void main() {
    vec2 uv = vUV * 2.0 - 1.0;
    float dist = length(uv);

    // Outside the tunnel opening — black
    if (dist < 0.05) {
        fragColour = vec4(0.0, 0.0, 0.0, 1.0);
        return;
    }

    // Map to cylindrical coordinates
    float angle = atan(uv.y, uv.x);  // -PI..PI
    float depth  = 0.3 / dist;        // hyperbolic depth (fisheye)

    float u = angle / 6.28318 + 0.5 + uScrollZ * 0.1;
    float v = depth + uTime * 0.5;

    // Tunnel grid pattern
    float gridU = abs(fract(u * 8.0) - 0.5) * 2.0;
    float gridV = abs(fract(v * 4.0) - 0.5) * 2.0;
    float grid  = step(0.85, max(gridU, gridV));

    // Colour: blue-green tunnel walls
    vec3 wallCol = vec3(0.0, 0.15, 0.3) * (1.0 - dist);
    vec3 gridCol = vec3(0.0, 0.5, 0.8);
    vec3 col = mix(wallCol, gridCol, grid * 0.6);

    // Fade at edges and centre
    float fade = smoothstep(0.0, 0.15, dist) * smoothstep(1.0, 0.8, dist);
    fragColour = vec4(col * fade, 1.0);
}
