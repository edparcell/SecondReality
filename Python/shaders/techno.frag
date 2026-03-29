#version 330 core

// Techno bars — EGA-style interference banding (TECHNO.EXE / JPLOGO)
//
// Replicates: horizontal stripe pattern cycling through EGA colour planes,
// with vertical scroll and beat-sync white flash.

in vec2 vUV;
out vec4 fragColour;

uniform float uTime;
uniform float uScroll;   // vertical scroll offset (CRTC start address equivalent)
uniform float uFlash;    // beat flash intensity [0..1]

// EGA 4-plane colour cycling: approximation of the 16 EGA colours
vec3 egaColour(int index) {
    // 16 EGA colours
    vec3 cols[16];
    cols[0]  = vec3(0.0,   0.0,   0.0);   // black
    cols[1]  = vec3(0.0,   0.0,   0.667); // dark blue
    cols[2]  = vec3(0.0,   0.667, 0.0);   // dark green
    cols[3]  = vec3(0.0,   0.667, 0.667); // dark cyan
    cols[4]  = vec3(0.667, 0.0,   0.0);   // dark red
    cols[5]  = vec3(0.667, 0.0,   0.667); // dark magenta
    cols[6]  = vec3(0.667, 0.333, 0.0);   // brown
    cols[7]  = vec3(0.667, 0.667, 0.667); // light grey
    cols[8]  = vec3(0.333, 0.333, 0.333); // dark grey
    cols[9]  = vec3(0.333, 0.333, 1.0);   // light blue
    cols[10] = vec3(0.333, 1.0,   0.333); // light green
    cols[11] = vec3(0.333, 1.0,   1.0);   // light cyan
    cols[12] = vec3(1.0,   0.333, 0.333); // light red
    cols[13] = vec3(1.0,   0.333, 1.0);   // light magenta
    cols[14] = vec3(1.0,   1.0,   0.333); // yellow
    cols[15] = vec3(1.0,   1.0,   1.0);   // white
    return cols[clamp(index, 0, 15)];
}

void main() {
    // Scrolled Y position
    float y = vUV.y + uScroll / 200.0;

    // Band index: determines which EGA colour this horizontal stripe uses
    float bandHeight = 0.025;    // height of each stripe (fraction of screen)
    int bandIndex    = int(floor(y / bandHeight));

    // Interference: XOR multiple wave frequencies (mirrors EGA bitplane cycling)
    int plane0 = int(floor(y * 16.0 + uTime * 4.0)) & 3;
    int plane1 = int(floor(y * 8.0  + uTime * 2.5)) & 3;
    int plane2 = int(floor(y * 32.0 + uTime * 7.0)) & 3;
    int planeXor = (plane0 ^ plane1 ^ plane2);

    // Map XOR plane value to EGA colour index, cycling over time
    int timeOffset = int(uTime * 3.0) & 15;
    int colIndex   = (bandIndex + planeXor * 4 + timeOffset) & 15;

    vec3 col = egaColour(colIndex);

    // Darken black bands (between stripes)
    float edge = abs(fract(y / bandHeight) - 0.5);
    if (edge > 0.45) col *= 0.3;

    // Beat flash
    col = mix(col, vec3(1.0), uFlash * 0.9);

    fragColour = vec4(col, 1.0);
}
