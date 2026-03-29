# Part 16: Vector Part II — Space Battle (U2E)

**Directory:** `original/VISU/C/` (same renderer as U2A)
**Output EXE:** `U2E.EXE`
**Coder:** PSI (renderer), All members (direction/scripting)

---

## Visual Effect

A fully choreographed 3D space battle scene rendered with the same flat-shaded polygon engine as the opening spaceship flyby. The scene features multiple spacecraft (fighters and a large command ship), asteroid field backgrounds, and camera moves that suggest camera tracking, close-ups, and wide establishing shots. Ships fire, one explodes, others manoeuvre. The script describes an extensive cinematic sequence.

---

## Scene Description (from SCRIPT / DESIGN)

The scene per the design document:
1. New camera angle with stars and the opening spaceship
2. Camera tracks around the large ship
3. Camera cuts to asteroid surface (horizon bitmap)
4. Two types of attack fighters are launched
5. Camera back to main ship, attackers in background
6. Camera follows attackers approaching
7. Camera from behind the main ship watching attackers
8. Camera from ship's side
9. Defence fighters launch
10. Wide shot: all ships approach
11. Battle begins — rapid cuts, X-wing style laser blasts
12. One attacker destroyed by missile
13. One defender destroyed — music marks the moment
14. All attackers destroyed nearly simultaneously
15. Fighter does a roll toward camera
16. Music calms — wide shot, large ship flies toward camera
17. Fade to black

---

## Technical Implementation

### Same Renderer as U2A

`U2E.EXE` uses the exact same `VISU/` renderer as `U2A.EXE`:
- `AMAIN.ASM` playback loop
- `AVID.ASM` / `ADRAW.ASM` rendering
- `ACALC.ASM` transforms
- `cfill()` in `MAIN.C` (C-side polygon fill)

### Scene Data

The scene is converted from 3DS/ASC source files in `original/3DS/`:
- `U2E.PRJ` — the main space battle scene project
- `PXLSHIP.3DS` / `PXLSHIP2.3DS` / `PXLSHIP3.3DS` — fighter ship models
- `I_SHP_3.3DS` — another ship variant
- `CITYBBK.3DS` — background geometry

Scene animation data from `.VUE` camera files defines all camera movements and object animation curves.

### Source Files (VISU/C/ — same as U2A)

| File | Purpose |
|---|---|
| `U2E.C` | Space battle specific scene playback |
| `U2EOLD.C` | Earlier version preserved |
| `CPLAY.C` | Camera/animation player |

### Object Z-Sorting

With multiple ships on screen simultaneously, the insertion-sort Z-sorter in `VISU/C/MAIN.C` sorts objects back-to-front each frame:
```c
for(a = 0; a < ordernum; a++) {
    dis = co[c = order[a]].dist;
    for(b = a-1; b >= 0 && dis > co[order[b]].dist; b--)
        order[b+1] = order[b];
    order[b+1] = c;
}
```

Objects with `_` prefix in their name always sort to background (skybox trick).

### Background City

`U2ABBK.C` and `U2AOK.C` handle a city background variant. The `cityflag` in the converter enables city-specific rendering paths where a bitmap city serves as a background element behind the 3D objects.

---

## Surprising Details

- The SCRIPT in Finnish describes the space battle as being in the style of the original "Unreal" demo by Future Crew — Second Reality was originally called "Unreal 2"
- The U2A/U2E renderer supports a background bitmap compositing mode (`U2ABBK.C`) where a pre-rendered city image sits behind the 3D objects
- 11 separate city scene project variants (`U2CITY2` through `U2CITY11`) indicate extensive iteration on the city background
- The space battle was described as requiring 500 polygons simultaneously — a significant number for 1993 real-time rendering
- The design notes reference "X-wing style paukkuja" (X-wing style blasts) — so laser fire was planned with particle/line effects between ships
