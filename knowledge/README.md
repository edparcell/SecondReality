# Second Reality — Knowledge Vault

This Obsidian vault documents the complete source code of **Second Reality** by The Future Crew (1993).

The goal is to understand the original demo thoroughly enough to recreate it in high definition using **Python, Pygame, and OpenGL**.

---

## Start Here

- [[Executive Summary]] — Overview, architecture, and team credits
- [[Architecture - Main Loader and DIS]] — How the demo runs: U2.EXE, DIS, STMIK

---

## Demo Sections (in order)

1. [[Parts - 01 Opening Credits (ALKU)]] — Movie-style text + widescreen horizon scroll
2. [[Parts - 02 Spaceship Flyby (U2A - VISU)]] — 3D spaceship flyby, full pipeline
3. [[Parts - 03 Explosion Animation (PAM)]] — Praxis ring explosion (pre-rendered FLI)
4. [[Parts - 04 Logo Reveal (BEG)]] — "Second Reality" title with bounce physics
5. [[Parts - 05 Glenz Vectors (GLENZ)]] — Semi-transparent polyhedra with glass shading
6. [[Parts - 06 Dot Tunnel (TUNNELI)]] — 512-dot particle tunnel/vortex
7. [[Parts - 07 Techno Bars (TECHNO)]] — Rotating EGA bars with palette effects
8. [[Parts - 08 Panic End (PANIC)]] — Screen shrinks to point (homage to Panic demo)
9. [[Parts - 09 Mountain Forest Scroll (FOREST)]] — Forest + logo scroll scene
10. [[Parts - 10 Lens and Rotozoomer (LENS)]] — Lens distortion + spinning zoom
11. [[Parts - 11 Plasma and Plasma Cube (PLZPART)]] — Summed-sine plasma + 3D cube
12. [[Parts - 12 Mini Vector Balls (DOTS - Grid)]] — Bouncing shaded dot-balls
13. [[Parts - 13 Mirror Ball Scroll (WATER)]] — Raytraced sphere + scrolling text
14. [[Parts - 14 3D Sinus Field Comanche (HARD)]] — Voxel height-field landscape
15. [[Parts - 15 Jelly Picture Interference (JPLOGO)]] — EGA interference + jelly reveal
16. [[Parts - 16 Vector Space Battle (U2E)]] — Full 3D space battle scene
17. [[Parts - 17 End Logo and Credits (END - CREDITS - ENDSCRL)]] — End sequence
- [[Parts - Hidden Desert Dream Stars (DDSTARS)]] — Hidden Easter egg
- [[Parts - Twist Effect (TWIST)]] — Cut/unused twist distortion effect

---

## Technical Reference

- [[Utilities and Shared Libraries]] — DIS, TWEAK, SIN tables, READP, FCP, GRAB tools
- [[Asset Inventory]] — Complete list of all graphics, music, and data assets
- [[Technical Reference - VGA Programming]] — VGA techniques and Python/OpenGL equivalents
- [[Development Workflow and Build System]] — Tools, compilers, build process
- [[Surprising and Notable Details]] — Easter eggs, Finnish design docs, clever tricks

---

## Repository Structure

```
SecondReality/
├── original/          ← Original unmodified source code
├── Python/            ← HD Python/Pygame/OpenGL recreation (future)
└── knowledge/         ← This Obsidian vault
```
