"""Enemy: blocky humanoid with chase AI, cheap obstacle steering, hit flash and a fall-over death."""
import math

from ursina import *

import config


class Enemy(Entity):
    def __init__(self, game, position, kind, wave):
        super().__init__(position=position)
        cfg = config.ENEMY_TYPES[kind]
        self.game = game
        self.player = game.player
        self.kind = kind
        self.alive = True
        self._removed = False

        self.scale = cfg["scale"]
        k = wave - 1
        self.max_health = cfg["health"] * (1 + 0.12 * k)
        self.health = self.max_health
        self.speed = cfg["speed"] * min(1.5, 1 + 0.04 * k)
        self.damage = cfg["damage"]
        self.attack_range = config.ENEMY_ATTACK_RANGE + 0.5 * (cfg["scale"] - 1)
        self.stop_distance = self.attack_range - 0.4

        self._atk_cd = 0.5
        self._attack_t = 0.0
        self._stagger = 0.0
        self._flash_t = 0.0
        self._walk = 0.0
        self._ray_t = 0.0
        self._side = Vec3(0, 0, 0)
        self._side_t = 0.0

        self._parts = []                         # (entity, base_color)
        skin = color.hsv(*cfg["skin"])
        cloth = color.hsv(*cfg["cloth"])
        dark = color.hsv(cfg["cloth"][0], 0.5, 0.2)
        self._cube(self, (0.62, 0.70, 0.36), (0, 1.15, 0), cloth)
        self._cube(self, (0.40, 0.40, 0.40), (0, 1.70, 0), skin)
        for sx in (-1, 1):
            self._cube(self, (0.08, 0.08, 0.03), (sx * 0.09, 1.74, 0.2), color.hsv(0, 1, 1))
        self.legs = []
        self.arms = []
        for sx in (-1, 1):
            leg = Entity(parent=self, position=(sx * 0.16, 0.8, 0))
            self._cube(leg, (0.26, 0.80, 0.26), (0, -0.4, 0), dark)
            self.legs.append(leg)
            arm = Entity(parent=self, position=(sx * 0.42, 1.45, 0))
            self._cube(arm, (0.18, 0.70, 0.18), (0, -0.3, 0), skin)
            self.arms.append(arm)

        self.collider = BoxCollider(self, center=Vec3(0, 1, 0), size=Vec3(1.0, 2.0, 0.8))
        if hasattr(self.player, "ignore_list"):
            self.player.ignore_list.append(self)   # player's ground/wall rays skip enemies

    def _cube(self, parent, scl, pos, col):
        e = Entity(parent=parent, model="cube", scale=scl, position=pos, color=col)
        self._parts.append((e, col))
        return e

    def _set_color(self, col):
        for e, base in self._parts:
            e.color = base if col is None else col

    # ------------------------------------------------------------- damage
    def take_damage(self, amount, headshot=False):
        """Returns True if this hit killed the enemy."""
        if not self.alive:
            return False
        self.health -= amount
        self._flash_t = 0.1
        self._stagger = 0.18
        self._set_color(color.red)
        dist = math.hypot(self.player.x - self.x, self.player.z - self.z)
        vol = max(0.25, 1 - dist / 60)
        if self.health <= 0:
            self._die(vol)
            return True
        if random_chance(0.5):
            self.game.audio.play("enemy_pain", volume=vol)
        return False

    def _die(self, vol):
        self.alive = False
        self.collider = None
        if hasattr(self.player, "ignore_list") and self in self.player.ignore_list:
            self.player.ignore_list.remove(self)
        self._set_color(color.hsv(0, 0.5, 0.25))
        self.game.audio.play("enemy_death", volume=vol)
        self.animate("rotation_x", -88, duration=0.45, curve=curve.in_quad)   # ragdoll-style topple
        invoke(self._shrink, delay=1.6)
        invoke(self._remove, delay=2.1)
        self.game.on_enemy_killed(self)

    def _shrink(self):
        if not self._removed:
            self.animate_scale(Vec3(0.01, 0.01, 0.01), duration=0.4)

    def _remove(self):
        if self._removed:
            return
        self._removed = True
        self.alive = False
        if hasattr(self.player, "ignore_list") and self in self.player.ignore_list:
            self.player.ignore_list.remove(self)
        destroy(self)

    # ----------------------------------------------------------------- AI
    def _probe(self, direction):
        """Look ahead for an obstacle; if blocked, pick the clearer side and strafe for a moment."""
        origin = Vec3(self.x, 0.8 * self.scale_y, self.z)
        ign = [self, self.player]
        hit = raycast(origin, direction, distance=1.8, ignore=ign, debug=False)
        if not hit.hit or isinstance(hit.entity, Enemy):
            self._side_t = 0.0
            return
        left = Vec3(-direction.z, 0, direction.x)
        dl = raycast(origin, (direction + left).normalized(), distance=3, ignore=ign, debug=False)
        dr = raycast(origin, (direction - left).normalized(), distance=3, ignore=ign, debug=False)
        left_room = dl.distance if dl.hit else 99
        right_room = dr.distance if dr.hit else 99
        self._side = left if left_room >= right_room else -left
        self._side_t = 0.6

    def update(self):
        if not self.alive:
            return
        dt = time.dt
        if self._flash_t > 0:
            self._flash_t -= dt
            if self._flash_t <= 0:
                self._set_color(None)
        if self.game.state != "playing":
            return

        player = self.player
        dx, dz = player.x - self.x, player.z - self.z
        dist = math.hypot(dx, dz) or 0.0001
        to_player = Vec3(dx / dist, 0, dz / dist)
        self.rotation_y = math.degrees(math.atan2(dx, dz))

        speed = self.speed * (0.35 if self._stagger > 0 else 1.0)
        self._stagger -= dt
        moving = dist > self.stop_distance
        if moving:
            move = to_player
            self._ray_t -= dt
            if self._ray_t <= 0:
                self._ray_t = 0.2 + (hash(id(self)) % 50) / 1000      # stagger rays across enemies
                self._probe(to_player)
            if self._side_t > 0:
                self._side_t -= dt
                move = to_player * 0.35 + self._side

            sep = Vec3(0, 0, 0)                                      # cheap boids-style separation
            for other in self.game.spawner.enemies:
                if other is self or not other.alive:
                    continue
                ox, oz = self.x - other.x, self.z - other.z
                d2 = ox * ox + oz * oz
                if 0.0001 < d2 < 1.44:
                    d = math.sqrt(d2)
                    sep += Vec3(ox / d, 0, oz / d) * (1.2 - d)
            move = (move + sep).normalized()

            lim = self.game.world.half - 1.5
            self.x = max(-lim, min(lim, self.x + move.x * speed * dt))
            self.z = max(-lim, min(lim, self.z + move.z * speed * dt))
            self._walk += dt * speed * 2.2

        # ---- attack ------------------------------------------------------
        if dist <= self.attack_range and abs(player.y - self.y) < 2.2:
            self._atk_cd -= dt
            if self._atk_cd <= 0:
                self._atk_cd = config.ENEMY_ATTACK_COOLDOWN
                self._attack_t = 0.35
                player.take_damage(self.damage)
        else:
            self._atk_cd = min(self._atk_cd, 0.4)

        # ---- procedural animation ---------------------------------------
        swing = math.sin(self._walk) * 35 if moving else 0
        self.legs[0].rotation_x = swing
        self.legs[1].rotation_x = -swing
        if self._attack_t > 0:
            self._attack_t -= dt
            lunge = -80 + math.sin(self._attack_t * 20) * 20
            self.arms[0].rotation_x = self.arms[1].rotation_x = lunge
        else:
            self.arms[0].rotation_x = -swing * 0.8 - 15
            self.arms[1].rotation_x = swing * 0.8 - 15


def random_chance(p):
    import random
    return random.random() < p
