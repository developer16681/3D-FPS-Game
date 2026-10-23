"""AudioManager: BGM + pooled SFX with graceful fallbacks.

Drop files into  assets/audio/  named exactly like the keys below
(.wav, .ogg or .mp3):

    bgm            looping combat music
    gunshot        weapon fire
    dry_fire       empty-magazine click
    reload         reload sound
    hit_marker     bullet hits an enemy
    enemy_pain     enemy damaged
    enemy_death    enemy killed
    player_hurt    player takes damage

Missing file  ->  ursfx procedural beep (if config.USE_PROCEDURAL_FALLBACK)
                  or silence. The game never crashes because of audio.
"""
import random
import time

from panda3d.core import Filename

import config

SFX_NAMES = ("gunshot", "dry_fire", "reload", "hit_marker",
             "enemy_pain", "enemy_death", "player_hurt")
MUSIC_NAME = "bgm"
EXTENSIONS = (".wav", ".ogg", ".mp3")
POOL_SIZES = {"gunshot": 6, "enemy_pain": 4, "hit_marker": 3, "enemy_death": 3}

# ursfx fallbacks: (volume_curve, kwargs). ursfx REQUIRES exactly 5 (time, volume) points.
PROCEDURAL = {
    "gunshot": ([(0.0, 0.0), (0.01, 1.0), (0.06, 0.55), (0.2, 0.15), (0.4, 0.0)],
                dict(volume=0.6, wave="noise", pitch=-12, pitch_change=-12, speed=4.0)),
    "dry_fire": ([(0.0, 0.0), (0.02, 1.0), (0.04, 0.3), (0.06, 0.6), (0.1, 0.0)],
                 dict(volume=0.4, wave="square", pitch=4, pitch_change=0, speed=3.0)),
    "reload": ([(0.0, 0.0), (0.05, 0.8), (0.15, 0.0), (0.4, 0.9), (0.55, 0.0)],
               dict(volume=0.35, wave="square", pitch=-2, pitch_change=6, speed=2.0)),
    "hit_marker": ([(0.0, 0.0), (0.02, 1.0), (0.06, 0.6), (0.09, 0.3), (0.12, 0.0)],
                   dict(volume=0.35, wave="sine", pitch=14, pitch_change=-4, speed=3.0)),
    "enemy_pain": ([(0.0, 0.0), (0.05, 0.9), (0.2, 0.5), (0.35, 0.25), (0.5, 0.0)],
                   dict(volume=0.4, wave="triangle", pitch=-4, pitch_change=-8, speed=2.0)),
    "enemy_death": ([(0.0, 0.0), (0.1, 0.9), (0.4, 0.6), (0.8, 0.3), (1.2, 0.0)],
                    dict(volume=0.5, wave="triangle", pitch=-12, pitch_change=-12, speed=1.0)),
    "player_hurt": ([(0.0, 0.0), (0.04, 1.0), (0.15, 0.5), (0.3, 0.2), (0.5, 0.0)],
                    dict(volume=0.5, wave="square", pitch=-10, pitch_change=-6, speed=2.0)),
}


class AudioManager:
    def __init__(self, loader):
        self._loader = loader
        self.master = config.MASTER_VOLUME
        self.music_volume = config.MUSIC_VOLUME
        self.sfx_volume = config.SFX_VOLUME
        self.muted = False
        self.on_volume_change = None      # callback(str) -> HUD toast

        self._pools = {}
        self._music = None
        self._last_proc = {}
        self._ursfx = None
        self._proc_ok = False

        if config.USE_PROCEDURAL_FALLBACK:
            try:
                from ursina.prefabs.ursfx import ursfx
                self._ursfx = ursfx
                self._proc_ok = True
            except Exception as exc:                      # noqa: BLE001
                print(f"[audio] ursfx unavailable ({exc}); missing sounds will be silent")

        missing = []
        for name in SFX_NAMES:
            path = self._find(name)
            sounds = [self._load(path) for _ in range(POOL_SIZES.get(name, 2))] if path else []
            sounds = [s for s in sounds if s is not None]
            if sounds:
                self._pools[name] = {"sounds": sounds, "i": 0}
            else:
                missing.append(name)

        music_path = self._find(MUSIC_NAME)
        if music_path:
            self._music = self._load(music_path)
            if self._music:
                self._music.setLoop(True)
        else:
            missing.append(MUSIC_NAME)

        if missing:
            mode = "procedural beeps" if self._proc_ok else "silence"
            print(f"[audio] no file in {config.AUDIO_DIR} for: {', '.join(missing)} -> {mode}"
                  f" (bgm is always silent when missing)")

    # ------------------------------------------------------------ loading
    @staticmethod
    def _find(name):
        for ext in EXTENSIONS:
            path = config.AUDIO_DIR / f"{name}{ext}"
            if path.is_file():
                return path
        return None

    def _load(self, path):
        try:
            return self._loader.loadSfx(Filename.fromOsSpecific(str(path)).getFullpath())
        except Exception as exc:                          # noqa: BLE001
            print(f"[audio] could not load {path.name}: {exc}")
            return None

    # ---------------------------------------------------------------- sfx
    def _level(self, volume=1.0):
        return 0.0 if self.muted else max(0.0, min(1.0, self.master * self.sfx_volume * volume))

    def play(self, name, volume=1.0, pitch_var=0.05):
        level = self._level(volume)
        if level <= 0.0:
            return
        pool = self._pools.get(name)
        if pool:
            snd = pool["sounds"][pool["i"]]
            pool["i"] = (pool["i"] + 1) % len(pool["sounds"])
            try:
                snd.stop()
                snd.setVolume(level)
                snd.setPlayRate(1.0 + random.uniform(-pitch_var, pitch_var))
                snd.play()
            except Exception:                             # noqa: BLE001
                pass
        elif self._proc_ok and name in PROCEDURAL:
            self._play_procedural(name, level)

    def _play_procedural(self, name, level):
        now = time.time()
        if now - self._last_proc.get(name, 0.0) < 0.05:   # ursfx synthesises on the CPU
            return
        self._last_proc[name] = now
        curve, kw = PROCEDURAL[name]
        kw = dict(kw)
        kw["volume"] = kw["volume"] * level
        try:
            self._ursfx(curve, **kw)
        except Exception as exc:                          # noqa: BLE001
            print(f"[audio] ursfx failed ({exc}); disabling procedural fallback")
            self._proc_ok = False

    # -------------------------------------------------------------- music
    def start_music(self):
        if self._music:
            self._apply_music_volume()
            self._music.play()

    def stop_music(self):
        if self._music:
            self._music.stop()

    def _apply_music_volume(self):
        if self._music:
            vol = 0.0 if self.muted else self.master * self.music_volume
            self._music.setVolume(max(0.0, min(1.0, vol)))

    # ------------------------------------------------------- volume keys
    def change_music(self, delta):
        self.music_volume = max(0.0, min(1.0, self.music_volume + delta))
        self._apply_music_volume()
        self._notify(f"Music volume: {round(self.music_volume * 100)}%")

    def change_sfx(self, delta):
        self.sfx_volume = max(0.0, min(1.0, self.sfx_volume + delta))
        self._notify(f"SFX volume: {round(self.sfx_volume * 100)}%")
        self.play("hit_marker")

    def toggle_mute(self):
        self.muted = not self.muted
        self._apply_music_volume()
        self._notify("Audio muted" if self.muted else "Audio on")

    def _notify(self, text):
        if self.on_volume_change:
            self.on_volume_change(text)
