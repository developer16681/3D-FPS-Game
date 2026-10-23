# Arena Shooter (Ursina FPS)

    pip install ursina
    python main.py

## Controls
| Key | Action |
|---|---|
| W A S D | move |
| Left Shift (+W) | sprint (FOV kick, wider crosshair) |
| Space | jump |
| Mouse | look (vertical clamped to ±90°) |
| Left Mouse (hold) | fire (full-auto) |
| R | reload; on the game-over/victory screen: restart |
| F1/F2 | music volume -/+ |
| F3/F4 | SFX volume -/+ |
| M | mute |
| Esc | quit |

## Layout
| File | Responsibility |
|---|---|
| `main.py` | window + entry point |
| `config.py` | **all** tunables (damage, waves, enemy types, volumes, pool sizes) |
| `game.py` | owns subsystems, state machine (playing/dead/won), restart |
| `player.py` | `FirstPersonController` subclass: sprint, FOV kick, health, regen |
| `weapon.py` | viewmodel, sway/bob/recoil (lerp), hitscan raycast, ammo, reload, muzzle flash |
| `enemy.py` | `Enemy`: chase AI, obstacle steering, red hit-flash, topple-over death |
| `spawn_manager.py` | wave spawner with a `MAX_ALIVE` cap, ammo/heal between waves |
| `hud.py` | dynamic crosshair, hit marker, ammo, health bar, kills, wave, end screen |
| `vfx.py` | pooled particles, tracers and bullet-hole decals (no per-shot allocation) |
| `audio_manager.py` | BGM + pooled SFX with safe fallbacks |
| `world.py` | ground, walls, cover, sky, fog |

## Audio files
Put files in `assets/audio/` (`.wav`, `.ogg` or `.mp3`), named exactly:

`bgm`, `gunshot`, `dry_fire`, `reload`, `hit_marker`, `enemy_pain`, `enemy_death`, `player_hurt`

Anything missing is replaced by a procedural `ursfx` beep (BGM falls back to silence), and a
one-line summary of what's missing is printed at startup. Set
`USE_PROCEDURAL_FALLBACK = False` in `config.py` for pure silence.

## Gameplay notes
- Headshots (upper body/head) deal ×2 damage; the hit marker turns orange for a headshot, red for a kill.
- Spread grows while moving, sprinting, airborne or firing; the crosshair shows it.
- Clearing a wave restores some health and reserve ammo. Survive `WAVES_TO_WIN` waves to win,
  or set `ENDLESS = True` for endless mode.
- The game uses Ursina's default unlit shader (no scene lights), so the muzzle flash is a bright
  emissive mesh rather than a real light.
