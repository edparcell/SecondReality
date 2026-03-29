#!/usr/bin/env python3
"""
Second Reality HD — Python/Pygame/OpenGL recreation
=====================================================
The Future Crew, 1993  |  HD recreation, 2026

Run:
    python main.py

Environment overrides:
    SECOND_REALITY_WIDTH=1920   # render width  (default 3840)
    SECOND_REALITY_HEIGHT=1080  # render height (default 2160)
    SECOND_REALITY_FULLSCREEN=1 # fullscreen mode

Controls:
    ESC        — exit
    Right →    — skip current part
"""

import os
import sys

# Allow running from the Python/ directory directly
sys.path.insert(0, os.path.dirname(__file__))

from demo.runner import Runner

# Import all parts in demo sequence order (mirrors U2.ASM part list)
from parts.p01_opening      import OpeningCredits
from parts.p02_spaceship    import SpaceshipFlyby
from parts.p03_explosion    import Explosion
from parts.p04_logo         import LogoReveal
from parts.p05_glenz        import GlenzVectors
from parts.p06_dot_tunnel   import DotTunnel
from parts.p07_techno       import TechnoBars
from parts.p08_panic        import PanicEnd
from parts.p09_forest       import ForestScroll
from parts.p10_lens         import LensRotozoomer
from parts.p11_plasma       import Plasma
from parts.p12_vector_balls import VectorBalls
from parts.p13_mirror_ball  import MirrorBallScroll
from parts.p14_voxel        import VoxelLandscape
from parts.p15_jelly        import JellyPicture
from parts.p16_space_battle import SpaceBattle
from parts.p17_credits      import Credits


def build_part_list():
    """Instantiate all parts in original demo order.
    Mirrors the exe sequence in original/MAIN/U2.ASM:
      ALKU → U2A → PAM → BEGLOGO → GLENZ → TUNNELI → TECHNO →
      PANICEND → MNTSCRL → LNS&ZOOM → PLZPART → MINVBALL →
      RAYSCRL → 3DSINFLD → JPLOGO → U2E → ENDLOGO/CRED/ENDSCRL
    """
    return [
        OpeningCredits(),    # ALKU.EXE       — opening credits on starfield
        SpaceshipFlyby(),    # U2A.EXE        — 3D spaceship flyby
        Explosion(),         # PAM.EXE        — explosion particle animation
        LogoReveal(),        # BEGLOGO.EXE    — "SECOND REALITY" logo reveal
        GlenzVectors(),      # GLENZ.EXE      — semi-transparent 3D object bounce
        DotTunnel(),         # TUNNELI.EXE    — 512-dot sphere→ring→tunnel phases
        TechnoBars(),        # TECHNO.EXE     — EGA interference bars + beat flash
        PanicEnd(),          # PANICEND.EXE   — "PANIC" text colour cycling
        ForestScroll(),      # MNTSCRL.EXE    — mountain/forest parallax scroll
        LensRotozoomer(),    # LNS&ZOOM.EXE   — lens distortion + rotozoomer
        Plasma(),            # PLZPART.EXE    — plasma summed-sine effect
        VectorBalls(),       # MINVBALL.EXE   — 3D grid metallic vector balls
        MirrorBallScroll(),  # RAYSCRL.EXE    — mirror-ball raycast scroller
        VoxelLandscape(),    # 3DSINFLD.EXE   — Comanche-style voxel heightmap
        JellyPicture(),      # JPLOGO.EXE     — jelly picture + interference reveal
        SpaceBattle(),       # U2E.EXE        — vector polygon space battle
        Credits(),           # ENDLOGO+CRED+ENDSCRL — end logo, credits, scroller
    ]


def main():
    fullscreen = bool(int(os.environ.get("SECOND_REALITY_FULLSCREEN", "0")))

    # Music files live alongside the original source
    music_dir = os.path.join(os.path.dirname(__file__),
                             '..', 'original', 'MAIN')
    music_dir = os.path.abspath(music_dir)

    parts = build_part_list()
    runner = Runner(parts, music_dir=music_dir, fullscreen=fullscreen)
    runner.run()


if __name__ == "__main__":
    main()
