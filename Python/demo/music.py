"""
Music subsystem — S3M playback via pygame.mixer.

Plays MUSIC0.S3M (intro sections) and MUSIC1.S3M (main/techno sections).

Row-level sync is approximated from elapsed playback time and a pre-measured
tempo.  S3M modules use a BPM/speed system; the default tempo for both tracks
is approximately 125 BPM at speed 6, giving ~20.83 rows/second.  Each pattern
has 64 rows, so one pattern lasts ~3.07 seconds.

For tighter sync a libopenmpt-based backend can be substituted by replacing
the _get_position() method — the rest of the API stays identical.

musplus() semantics (mirrors original DIS):
  Normally returns -100 (running, far from any exit cue).
  Returns a value in range (-15, -1) for NUM_EXIT_FRAMES frames when a
  timed exit cue fires — parts check `if a < 0 and a > -16: break`.
  Returns 0 when music has fully stopped.
"""

import os
import time
import pygame


# Default S3M playback parameters (both tracks use these)
_DEFAULT_BPM = 125
_DEFAULT_SPEED = 6
_ROWS_PER_BEAT = 1
_TICKS_PER_ROW = _DEFAULT_SPEED
_BPM = _DEFAULT_BPM
# rows per second = BPM * 2 / (speed * 5)  (standard S3M timing formula)
_ROWS_PER_SEC = (_BPM * 2) / (_TICKS_PER_ROW * 5)  # ~10.0 rows/sec at 125bpm/6

# How many frames the exit cue is held active (so parts have time to catch it)
_EXIT_CUE_FRAMES = 30

# Timed exit cues for each track: list of (elapsed_seconds, cue_value) tuples.
# cue_value must be in range (-15, -1) exclusive of -15 and -1 boundaries.
# These are approximate — calibrate against actual playback if needed.
_MUSIC0_EXIT_CUES: list[tuple[float, int]] = [
    (30.0, -2),   # end of opening section
]

_MUSIC1_EXIT_CUES: list[tuple[float, int]] = [
    (22.0,  -2),   # after logo/glenz
    (44.0,  -3),   # after tunnel/techno
    (66.0,  -4),   # after panic/forest
    (90.0,  -5),   # after lens/plasma
    (115.0, -6),   # after vector balls/mirror
    (138.0, -7),   # after voxel/jelly
    (160.0, -8),   # after space battle
    (185.0, -9),   # after credits
]


class MusicPlayer:
    def __init__(self, music_dir: str):
        self._music_dir = music_dir
        self._start_time: float = 0.0
        self._playing: bool = False
        self._track: int = 0
        self._exit_cues: list[tuple[float, int]] = []
        self._active_cue: int = -100   # current musplus() return value
        self._active_cue_until: float = 0.0
        self._cue_index: int = 0

        # Ensure mixer is initialised (runner.py does this, but be safe)
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)

    def load(self, track: int) -> None:
        """Load track 0 (MUSIC0.S3M) or track 1 (MUSIC1.S3M)."""
        self._track = track
        name = f"MUSIC{track}.S3M"
        path = os.path.join(self._music_dir, name)
        if not os.path.exists(path):
            print(f"[music] WARNING: {path} not found — running without music")
            return
        try:
            pygame.mixer.music.load(path)
            print(f"[music] Loaded {name}")
        except pygame.error as e:
            print(f"[music] Could not load {name}: {e}")

    def play(self, start_row: int = 0) -> None:
        """Start playback. start_row is ignored (pygame.mixer doesn't expose it)."""
        self._exit_cues = _MUSIC0_EXIT_CUES if self._track == 0 else _MUSIC1_EXIT_CUES
        self._cue_index = 0
        self._active_cue = -100
        self._active_cue_until = 0.0
        try:
            pygame.mixer.music.play(loops=-1)
        except pygame.error:
            pass
        self._start_time = time.monotonic()
        self._playing = True

    def stop(self) -> None:
        try:
            pygame.mixer.music.stop()
        except pygame.error:
            pass
        self._playing = False

    def fade(self, volume: float) -> None:
        """Set volume 0.0..1.0."""
        try:
            pygame.mixer.music.set_volume(max(0.0, min(1.0, volume)))
        except pygame.error:
            pass

    def fade_out(self, frames: int, fps: float = 60.0) -> None:
        """Begin a fade-out over `frames` frames (call fade() each frame instead
        for gradual control from the part itself)."""
        ms = int(frames / fps * 1000)
        try:
            pygame.mixer.music.fadeout(ms)
        except pygame.error:
            pass

    # ------------------------------------------------------------------
    # DIS-compatible sync interface
    # ------------------------------------------------------------------

    def elapsed(self) -> float:
        """Seconds since playback started."""
        if not self._playing:
            return 0.0
        return time.monotonic() - self._start_time

    def musrow(self) -> int:
        """Current S3M row approximation (0..63)."""
        row_total = int(self.elapsed() * _ROWS_PER_SEC)
        return row_total % 64

    def musplus(self) -> int:
        """Returns the current music sync code.
        -100: playing normally
        -15..-2: exit cue active
        0: stopped
        """
        if not self._playing:
            return 0

        now = self.elapsed()

        # Check if a new exit cue fires
        if self._cue_index < len(self._exit_cues):
            cue_time, cue_val = self._exit_cues[self._cue_index]
            if now >= cue_time:
                self._active_cue = cue_val
                self._active_cue_until = now + (_EXIT_CUE_FRAMES / 60.0)
                self._cue_index += 1

        # Return active cue while it's still in the window
        if now < self._active_cue_until:
            return self._active_cue

        return -100
