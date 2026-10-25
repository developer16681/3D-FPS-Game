"""Central tunables for the whole game. Tweak values here, not in the logic."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
AUDIO_DIR = BASE_DIR / "assets" / "audio"

TITLE = "ARENA SHOOTER"

# ---------------------------------------------------------------- world
ARENA_SIZE = 80
WALL_HEIGHT = 6
OBSTACLE_COUNT = 16
WORLD_SEED = 7

# --------------------------------------------------------------- player
PLAYER_MAX_HEALTH = 100
WALK_SPEED = 6
SPRINT_SPEED = 10
JUMP_HEIGHT = 1.6
MOUSE_SENSITIVITY = (40, 40)
BASE_FOV = 90
SPRINT_FOV = 100
REGEN_DELAY = 6.0          # seconds without damage before regen starts
REGEN_RATE = 5.0           # hp / second

# --------------------------------------------------------------- weapons
WEAPONS = {
    "pistol":  dict(mag=12, reserve=60,  max_reserve=120, interval=0.25, damage=35, pellets=1,
                    pellet_spread=0.0,  reload=1.2, auto=False, recoil=0.7,  kick=0.6),
    "rifle":   dict(mag=30, reserve=90,  max_reserve=180, interval=0.11, damage=20, pellets=1,
                    pellet_spread=0.0,  reload=1.6, auto=True,  recoil=1.0,  kick=0.7),
    "smg":     dict(mag=40, reserve=120, max_reserve=240, interval=0.07, damage=12, pellets=1,
                    pellet_spread=0.01, reload=1.5, auto=True,  recoil=0.6,  kick=0.5),
    "shotgun": dict(mag=6,  reserve=24,  max_reserve=48,  interval=0.85, damage=10, pellets=8,
                    pellet_spread=0.08, reload=2.4, auto=False, recoil=2.2,  kick=2.0),
    "sniper":  dict(mag=5,  reserve=20,  max_reserve=40,  interval=1.2,  damage=110, pellets=1,
                    pellet_spread=0.0,  reload=2.8, auto=False, recoil=2.5,  kick=2.5),
}
START_WEAPONS = ["pistol", "rifle", "shotgun"]
AMMO_PER_WAVE = 30         # reserve ammo granted per gun when a wave is cleared
HEAL_PER_WAVE = 25         # hp granted when a wave is cleared
HEADSHOT_MULT = 2.0
HEAD_HEIGHT = 1.5          # hit height / enemy scale above which it's a headshot
MAX_RANGE = 150
AUTO_RELOAD_ON_EMPTY = True

# ---------------------------------------------------------------- enemy
# colours are HSV tuples (hue 0-360, sat 0-1, val 0-1)
ENEMY_TYPES = {
    "grunt":    dict(health=60,  speed=3.2, damage=8,  scale=1.00, weight=7, min_wave=1,
                     skin=(95, 0.45, 0.55),  cloth=(215, 0.40, 0.35)),
    "runner":   dict(health=35,  speed=5.6, damage=6,  scale=0.88, weight=5, min_wave=2,
                     skin=(30, 0.45, 0.75),  cloth=(0, 0.55, 0.45)),
    "brute":    dict(health=180, speed=2.2, damage=18, scale=1.35, weight=4, min_wave=4,
                     skin=(280, 0.30, 0.50), cloth=(35, 0.50, 0.30)),
    "stalker":  dict(health=95,  speed=4.5, damage=14, scale=1.05, weight=4, min_wave=7,
                     skin=(180, 0.60, 0.60), cloth=(220, 0.60, 0.25)),
    "titan":    dict(health=380, speed=2.0, damage=28, scale=1.60, weight=3, min_wave=11,
                     skin=(10, 0.75, 0.45),  cloth=(0, 0.85, 0.25)),
    "overlord": dict(health=750, speed=2.4, damage=35, scale=1.90, weight=2, min_wave=16,
                     skin=(290, 0.80, 0.70), cloth=(45, 0.90, 0.50)),
}
ENEMY_ATTACK_RANGE = 1.9
ENEMY_ATTACK_COOLDOWN = 1.0

# -------------------------------------------------------------- spawning
WAVES_TO_WIN = 20
ENDLESS = False            # True -> never show the victory screen
ENEMIES_BASE = 5
ENEMIES_PER_WAVE = 2       # scales smoothly up to 43 total enemies at wave 20
MAX_ALIVE = 18             # performance cap on simultaneous enemies
SPAWN_INTERVAL = 0.8
INTERMISSION = 3.5
SPAWN_MIN_DIST = 22
SPAWN_MAX_DIST = 38

# ----------------------------------------------------------------- audio
MASTER_VOLUME = 0.8
MUSIC_VOLUME = 0.35
SFX_VOLUME = 0.9
USE_PROCEDURAL_FALLBACK = True   # use ursfx beeps when a .wav/.ogg is missing

# ------------------------------------------------------------------- vfx
PARTICLE_POOL = 160
TRACER_POOL = 8
DECAL_POOL = 32
