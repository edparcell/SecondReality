#version 330 core

// Mirror ball — raycast chrome sphere with environment reflection

in vec2 vUV;
out vec4 fragColour;

uniform float uTime;
uniform float uAspect;
uniform float uScroll;

// Environment: starfield + gradient sky
vec3 environment(vec3 dir) {
    // Sky gradient
    vec3 sky = mix(vec3(0.02, 0.03, 0.15), vec3(0.0, 0.0, 0.02),
                   clamp(dir.y * 0.5 + 0.5, 0.0, 1.0));

    // Stars: hash-based
    vec3 sd = normalize(dir);
    vec2 uv = vec2(atan(sd.z, sd.x) / 6.28318, asin(sd.y) / 3.14159);
    uv = fract(uv * vec2(31.7, 17.3));
    float star = step(0.97, fract(sin(dot(floor(uv * 60.0),
                       vec2(127.1, 311.7))) * 43758.5));
    sky += vec3(1.0) * star * 2.0;

    // Light source (white spotlight)
    float spot = pow(max(0.0, dot(dir, normalize(vec3(0.5, 1.0, 0.8)))), 64.0);
    sky += vec3(1.5) * spot;

    return sky;
}

void main() {
    vec2 uv = vUV * 2.0 - 1.0;
    uv.x   *= uAspect;

    // Ray setup: orthographic from front
    vec3 ro = vec3(uv.x, uv.y + 0.1, 3.0);
    vec3 rd = vec3(0.0, 0.0, -1.0);

    // Ball position: slow oscillation
    vec3 ballPos = vec3(sin(uTime * 0.4) * 0.3, 0.3 + cos(uTime * 0.3) * 0.1, 0.0);
    float ballR  = 0.5;

    vec3 col = vec3(0.0);

    // Ray-sphere intersection
    vec3 oc = ro - ballPos;
    float a = dot(rd, rd);
    float b = 2.0 * dot(oc, rd);
    float c = dot(oc, oc) - ballR * ballR;
    float disc = b*b - 4.0*a*c;

    if (disc >= 0.0) {
        float t = (-b - sqrt(disc)) / (2.0 * a);
        if (t > 0.0) {
            vec3 hitPos = ro + rd * t;
            vec3 normal = normalize(hitPos - ballPos);

            // Mirror ball: discrete facets (tile normal to facet grid)
            float facetScale = 12.0;
            vec3 fn = normalize(floor(normal * facetScale + 0.5) / facetScale);

            // Reflection direction
            vec3 reflDir = reflect(rd, fn);

            // Rotation of the ball
            float angle = uTime * 0.5;
            float c_ = cos(angle); float s_ = sin(angle);
            reflDir.xz = vec2(c_*reflDir.x - s_*reflDir.z,
                              s_*reflDir.x + c_*reflDir.z);

            col = environment(reflDir);

            // Edge darkening (sphere shadow)
            float rim = 1.0 - abs(dot(normal, -rd));
            col *= (1.0 - rim * rim * 0.3);
        }
    } else {
        // Background: night sky
        col = environment(rd);
    }

    // Ground plane (below ball)
    if (uv.y < -0.2) {
        float gx = uv.x + uScroll;
        float gy = (uv.y + 0.2) / 0.2;
        // Checkerboard floor
        float check = mod(floor(gx * 8.0) + floor(gy * 8.0), 2.0);
        vec3 floorCol = mix(vec3(0.02, 0.02, 0.08), vec3(0.1, 0.1, 0.3), check);
        floorCol *= (1.0 - gy * gy);  // fade to black at bottom
        // Ball shadow
        float shadowDist = length(uv.xy - ballPos.xy * vec2(1.0/uAspect, 1.0) - vec2(0.0, -0.25));
        floorCol *= (1.0 - smoothstep(0.2, 0.5, shadowDist) * 0.5);
        col = mix(col, floorCol, smoothstep(-0.18, -0.22, uv.y));
    }

    fragColour = vec4(col, 1.0);
}
