"""Wave-based spawn manager with a hard cap on simultaneous enemies."""
import math
import random

from ursina import *

import config
from enemy import Enemy


class SpawnManager(Entity):
    def __init__(self, game):
        super().__init__()
        self.game = game
        self.enemies = []
        self.reset()

    def reset(self):
        for e in self.enemies:
            e._remove()
        self.enemies = []
        self.wave = 0
        self.to_spawn = 0
        self.spawn_timer = 0.0
        self.state = "intermission"
        self.timer = 2.5

    @property
    def alive_count(self):
        return sum(1 for e in self.enemies if e.alive)

    # ------------------------------------------------------------- waves
    def _start_wave(self):
        self.wave += 1
        self.to_spawn = config.ENEMIES_BASE + (self.wave - 1) * config.ENEMIES_PER_WAVE
        self.spawn_timer = 0.0
        self.state = "active"
        self.game.hud.set_wave(self.wave)
        self.game.hud.banner(f"WAVE {self.wave}", 2.0)

    def _wave_cleared(self):
        if self.wave >= config.WAVES_TO_WIN and not config.ENDLESS:
            self.game.finish(win=True)
            return
        self.game.player.heal(config.HEAL_PER_WAVE)
        self.game.weapon.add_reserve(config.AMMO_PER_WAVE)
        self.game.hud.banner(f"WAVE {self.wave} CLEARED", 2.5)
        self.state = "intermission"
        self.timer = config.INTERMISSION

    # ---------------------------------------------------------- spawning
    def _pick_kind(self):
        kinds, weights = [], []
        for name, cfg in config.ENEMY_TYPES.items():
            if self.wave >= cfg["min_wave"]:
                kinds.append(name)
                weights.append(cfg["weight"])
        return random.choices(kinds, weights)[0]

    def _spawn_position(self):
        p = self.game.player
        lim = self.game.world.half - 3
        for _ in range(14):
            ang = random.uniform(0, math.tau)
            r = random.uniform(config.SPAWN_MIN_DIST, config.SPAWN_MAX_DIST)
            x = max(-lim, min(lim, p.x + math.cos(ang) * r))
            z = max(-lim, min(lim, p.z + math.sin(ang) * r))
            if (math.hypot(x - p.x, z - p.z) >= config.SPAWN_MIN_DIST * 0.8
                    and self.game.world.point_free(x, z, 1.5)):
                return Vec3(x, 0, z)
        return Vec3(-p.x * 0.9, 0, -p.z * 0.9 + lim * 0.5)

    def _spawn_one(self):
        self.enemies.append(Enemy(self.game, self._spawn_position(), self._pick_kind(), self.wave))
        self.to_spawn -= 1

    # ------------------------------------------------------------ update
    def update(self):
        if self.game.state != "playing":
            return
        dt = time.dt
        self.enemies = [e for e in self.enemies if not e._removed]

        if self.state == "intermission":
            self.timer -= dt
            if self.timer <= 0:
                self._start_wave()
            return

        if self.to_spawn > 0:
            self.spawn_timer -= dt
            if self.spawn_timer <= 0 and self.alive_count < config.MAX_ALIVE:
                self._spawn_one()
                self.spawn_timer = config.SPAWN_INTERVAL
        elif self.alive_count == 0:
            self._wave_cleared()
