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

# --------------------------------------------------------------- weapon
MAG_SIZE = 30
START_RESERVE = 90
MAX_RESERVE = 180
AMMO_PER_WAVE = 60         # reserve ammo granted when a wave is cleared
HEAL_PER_WAVE = 25         # hp granted when a wave is cleared
FIRE_INTERVAL = 0.11       # seconds between shots (full-auto while held)
RELOAD_TIME = 1.6
DAMAGE = 20
HEADSHOT_MULT = 2.0
HEAD_HEIGHT = 1.5          # hit height / enemy scale above which it's a headshot
MAX_RANGE = 150
AUTO_RELOAD_ON_EMPTY = True

# ---------------------------------------------------------------- enemy
# colours are HSV tuples (hue 0-360, sat 0-1, val 0-1)
ENEMY_TYPES = {
    "grunt":  dict(health=60,  speed=3.2, damage=8,  scale=1.00, weight=6, min_wave=1,
                   skin=(95, 0.45, 0.55),  cloth=(215, 0.40, 0.35)),
    "runner": dict(health=35,  speed=5.6, damage=6,  scale=0.88, weight=3, min_wave=2,
                   skin=(30, 0.45, 0.75),  cloth=(0, 0.55, 0.45)),
    "brute":  dict(health=180, speed=2.2, damage=18, scale=1.35, weight=2, min_wave=3,
                   skin=(280, 0.30, 0.50), cloth=(35, 0.50, 0.30)),
}
ENEMY_ATTACK_RANGE = 1.9
ENEMY_ATTACK_COOLDOWN = 1.0

# -------------------------------------------------------------- spawning
WAVES_TO_WIN = 5
ENDLESS = False            # True -> never show the victory screen
ENEMIES_BASE = 5
ENEMIES_PER_WAVE = 3
MAX_ALIVE = 14             # performance cap on simultaneous enemies
SPAWN_INTERVAL = 0.9
INTERMISSION = 4.0
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
