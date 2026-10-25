"""Weapon: viewmodel parented to the camera, multi-weapon loadout, sway/bob/recoil,
hitscan raycast, ammo & reload, shotguns & sniper scope.
"""
import random
from math import sin, pi

from ursina import *

import config
from enemy import Enemy


class Weapon(Entity):
    BASE_POS = Vec3(0.32, -0.28, 0.62)

    def __init__(self, game):
        super().__init__(parent=camera, position=Weapon.BASE_POS)
        self.game = game

        self.models = {}
        for name in config.WEAPONS:
            self.models[name] = self._build_model(name)

        self.sway = Vec3(0, 0, 0)
        self.bob_phase = 0.0
        self.bob_amount = 0.0
        self.sprint_blend = 0.0
        self.recoil = 0.0
        self.recoil_target = 0.0
        self.fire_kick = 0.0
        self.spread = 0.0                  # 0..1, read by the HUD crosshair
        self._pitch_pending = 0.0
        self._flash_t = 0.0
        self._trigger_pressed = False
        self.is_scoped = False
        self.reset()

    # --------------------------------------------------------------- models
    def _build_model(self, name):
        root = Entity(parent=self, enabled=False)

        dark = color.hsv(220, 0.10, 0.18)
        mid = color.hsv(220, 0.08, 0.32)
        accent = color.hsv(30, 0.7, 0.6)

        if name == "pistol":
            Entity(parent=root, model="cube", scale=(0.065, 0.085, 0.24), position=(0, 0, 0.02), color=dark)
            Entity(parent=root, model="cube", scale=(0.05, 0.04, 0.22), position=(0, 0.05, 0.03), color=mid)
            Entity(parent=root, model="cube", scale=(0.05, 0.13, 0.06), position=(0, -0.09, -0.04),
                   rotation_x=-18, color=mid)
            Entity(parent=root, model="cube", scale=(0.01, 0.015, 0.01), position=(0, 0.075, 0.12), color=accent)
            muzzle = Entity(parent=root, position=(0, 0.03, 0.16))

        elif name == "rifle":
            Entity(parent=root, model="cube", scale=(0.085, 0.11, 0.42), position=(0, 0, 0.05), color=dark)
            Entity(parent=root, model="cube", scale=(0.07, 0.05, 0.38), position=(0, 0.075, 0.07), color=mid)
            Entity(parent=root, model="cube", scale=(0.035, 0.035, 0.30), position=(0, 0.015, 0.38), color=dark)
            Entity(parent=root, model="cube", scale=(0.07, 0.17, 0.07), position=(0, -0.12, -0.07),
                   rotation_x=-15, color=mid)
            Entity(parent=root, model="cube", scale=(0.06, 0.14, 0.08), position=(0, -0.11, 0.12), color=dark)
            Entity(parent=root, model="cube", scale=(0.012, 0.025, 0.012), position=(0, 0.11, 0.2), color=accent)
            muzzle = Entity(parent=root, position=(0, 0.015, 0.56))

        elif name == "smg":
            Entity(parent=root, model="cube", scale=(0.075, 0.095, 0.30), position=(0, 0, 0.03), color=dark)
            Entity(parent=root, model="cube", scale=(0.06, 0.045, 0.26), position=(0, 0.06, 0.04), color=mid)
            Entity(parent=root, model="cube", scale=(0.03, 0.03, 0.18), position=(0, 0.01, 0.28), color=dark)
            Entity(parent=root, model="cube", scale=(0.055, 0.18, 0.055), position=(0, -0.13, 0.06),
                   rotation_x=5, color=dark)
            Entity(parent=root, model="cube", scale=(0.06, 0.14, 0.06), position=(0, -0.10, -0.08),
                   rotation_x=-15, color=mid)
            Entity(parent=root, model="cube", scale=(0.01, 0.02, 0.01), position=(0, 0.09, 0.14), color=accent)
            muzzle = Entity(parent=root, position=(0, 0.01, 0.40))

        elif name == "shotgun":
            Entity(parent=root, model="cube", scale=(0.095, 0.11, 0.36), position=(0, 0, 0.02), color=mid)
            # Twin barrels
            Entity(parent=root, model="cube", scale=(0.032, 0.032, 0.38), position=(-0.022, 0.03, 0.32), color=dark)
            Entity(parent=root, model="cube", scale=(0.032, 0.032, 0.38), position=(0.022, 0.03, 0.32), color=dark)
            # Pump handle and stock
            Entity(parent=root, model="cube", scale=(0.085, 0.07, 0.14), position=(0, -0.01, 0.24), color=accent)
            Entity(parent=root, model="cube", scale=(0.07, 0.12, 0.22), position=(0, -0.08, -0.16),
                   rotation_x=-8, color=mid)
            muzzle = Entity(parent=root, position=(0, 0.03, 0.54))

        elif name == "sniper":
            Entity(parent=root, model="cube", scale=(0.08, 0.10, 0.46), position=(0, 0, 0.05), color=dark)
            Entity(parent=root, model="cube", scale=(0.032, 0.032, 0.55), position=(0, 0.02, 0.50), color=dark)
            # Muzzle brake
            Entity(parent=root, model="cube", scale=(0.045, 0.045, 0.08), position=(0, 0.02, 0.80), color=mid)
            # Scope tube and mount
            Entity(parent=root, model="cube", scale=(0.025, 0.04, 0.18), position=(0, 0.08, 0.05), color=mid)
            Entity(parent=root, model="cube", scale=(0.05, 0.05, 0.32), position=(0, 0.12, 0.05), color=dark)
            Entity(parent=root, model="cube", scale=(0.06, 0.06, 0.05), position=(0, 0.12, 0.20), color=accent)
            Entity(parent=root, model="cube", scale=(0.06, 0.15, 0.07), position=(0, -0.11, -0.08),
                   rotation_x=-15, color=mid)
            Entity(parent=root, model="cube", scale=(0.07, 0.10, 0.22), position=(0, -0.06, -0.22), color=dark)
            muzzle = Entity(parent=root, position=(0, 0.02, 0.85))

        else:
            muzzle = Entity(parent=root, position=(0, 0, 0.5))

        flash = Entity(parent=muzzle, enabled=False)
        Entity(parent=flash, model="sphere", scale=0.1, color=color.yellow)
        Entity(parent=flash, model="quad", scale=0.32, color=color.orange)
        Entity(parent=flash, model="quad", scale=0.32, rotation_z=45, z=0.01, color=color.yellow)

        root.muzzle = muzzle
        root.flash = flash
        return root

    # --------------------------------------------------------------- state
    def reset(self):
        self.loadout = {n: dict(mag=c["mag"], reserve=c["reserve"])
                        for n, c in config.WEAPONS.items()}
        self.current = "rifle"
        self._equip(self.current)
        self.cooldown = 0.0
        self.reloading = False
        self.reload_timer = 0.0
        self.recoil = self.recoil_target = self.fire_kick = self.spread = 0.0
        self._pitch_pending = 0.0
        self._flash_t = 0.0
        self.is_scoped = False
        self.position = Weapon.BASE_POS
        self.rotation = Vec3(0, 0, 0)

    def _equip(self, name):
        if name not in config.WEAPONS:
            return
        self.current = name
        self.stats = config.WEAPONS[name]
        for n, m in self.models.items():
            m.enabled = (n == name)
        self.muzzle = self.models[name].muzzle
        self.flash = self.models[name].flash
        self.reloading = False
        self.cooldown = 0.25                      # short draw delay
        self.is_scoped = False

    @property
    def mag(self):
        return self.loadout[self.current]["mag"]

    @mag.setter
    def mag(self, v):
        self.loadout[self.current]["mag"] = v

    @property
    def reserve(self):
        return self.loadout[self.current]["reserve"]

    @reserve.setter
    def reserve(self, v):
        self.loadout[self.current]["reserve"] = v

    def add_reserve(self, amount):
        for name, g in self.loadout.items():
            max_res = config.WEAPONS[name].get("max_reserve", 180)
            g["reserve"] = min(max_res, g["reserve"] + amount)

    # --------------------------------------------------------------- input
    def input(self, key):
        keys = {"1": "pistol", "2": "rifle", "3": "shotgun", "4": "smg", "5": "sniper"}
        if key in keys and keys[key] != self.current:
            self._equip(keys[key])
            self.game.audio.play("reload", volume=0.4)
        elif key in ("scroll up", "scroll down"):
            names = list(config.WEAPONS)
            i = names.index(self.current)
            delta = 1 if key == "scroll up" else -1
            self._equip(names[(i + delta) % len(names)])
            self.game.audio.play("reload", volume=0.4)
        elif key == "left mouse down":
            self._trigger_pressed = True
        elif key == "r":
            self.start_reload()

    def start_reload(self):
        if self.reloading or self.mag >= self.stats["mag"] or self.reserve <= 0:
            return
        self.reloading = True
        self.reload_timer = self.stats["reload"]
        self.game.audio.play("reload")

    def _finish_reload(self):
        take = min(self.stats["mag"] - self.mag, self.reserve)
        self.mag += take
        self.reserve -= take
        self.reloading = False

    # ------------------------------------------------------------- shooting
    def _dry_fire(self):
        self.cooldown = 0.25
        self.game.audio.play("dry_fire")
        if config.AUTO_RELOAD_ON_EMPTY:
            self.start_reload()

    def _fire(self):
        p = self.game.player
        self.mag -= 1
        self.cooldown = self.stats["interval"]
        self.recoil_target = self.stats["recoil"]
        self.fire_kick = min(1.0, self.fire_kick + 0.18 * self.stats["kick"])
        self._pitch_pending += random.uniform(0.5, 0.9) * self.stats["kick"]
        p.rotation_y += random.uniform(-0.2, 0.2) * self.stats["kick"]

        self._flash_t = 0.04
        self.flash.enabled = True
        self.flash.scale = random.uniform(0.8, 1.3)
        self.flash.rotation_z = random.uniform(0, 360)

        # Play weapon-specific gunshot sound or fallback
        self.game.audio.play(f"gunshot_{self.current}")
        self._shoot_ray()

    def _shoot_ray(self):
        game = self.game
        pellets = self.stats.get("pellets", 1)
        pellet_spread = self.stats.get("pellet_spread", 0.0)

        for _ in range(pellets):
            jitter = self.spread * 0.035 + pellet_spread
            direction = (camera.forward
                         + camera.right * random.uniform(-jitter, jitter)
                         + camera.up * random.uniform(-jitter, jitter)).normalized()
            origin = camera.world_position
            hit = raycast(origin, direction, distance=config.MAX_RANGE, ignore=[game.player], debug=False)

            end = hit.world_point if hit.hit else origin + direction * 80
            game.vfx.tracer(self.muzzle.world_position, end)
            if not hit.hit:
                continue

            ent = hit.entity
            if isinstance(ent, Enemy) and ent.alive:
                head = (hit.world_point.y - ent.y) / ent.scale_y >= config.HEAD_HEIGHT
                base_dmg = self.stats["damage"]
                # Optional distance falloff for shotgun
                if self.current == "shotgun":
                    falloff = clamp(1.0 - hit.distance / 25.0, 0.25, 1.0)
                    base_dmg *= falloff
                dmg = base_dmg * (config.HEADSHOT_MULT if head else 1.0)
                killed = ent.take_damage(dmg, headshot=head)
                game.vfx.blood(hit.world_point, hit.world_normal)
                game.hud.hit_marker(kill=killed, head=head)
                game.audio.play("hit_marker")
            else:
                game.vfx.impact(hit.world_point, hit.world_normal)
                game.vfx.decal(hit.world_point, hit.world_normal)

    # -------------------------------------------------------------- update
    def update(self):
        dt = time.dt
        p = self.game.player
        self.cooldown = max(0.0, self.cooldown - dt)

        # Sniper scope logic (right mouse held)
        is_sniper = (self.current == "sniper")
        self.is_scoped = is_sniper and bool(held_keys["right mouse"]) and mouse.locked

        current_model = self.models.get(self.current)
        if current_model:
            current_model.enabled = not self.is_scoped

        if self.reloading:
            self.reload_timer -= dt
            if self.reload_timer <= 0:
                self._finish_reload()

        auto_mode = self.stats.get("auto", True)
        held = bool(held_keys["left mouse"]) and mouse.locked if auto_mode else False
        pressed = self._trigger_pressed and mouse.locked
        self._trigger_pressed = False

        if self.cooldown <= 0 and not self.reloading:
            if self.mag > 0 and (held or pressed):
                self._fire()
            elif self.mag <= 0 and pressed:
                self._dry_fire()

        # ---- crosshair spread (0..1) -------------------------------------
        target = 0.0
        if p.moving:
            target += 0.25
        if p.sprinting:
            target += 0.15
        if not p.grounded:
            target += 0.3
        if self.is_scoped:
            target = 0.0

        self.fire_kick = max(0.0, self.fire_kick - dt * 1.4)
        target = min(1.0, target + self.fire_kick)
        self.spread = lerp(self.spread, target, min(1.0, dt * 10))

        # ---- recoil: snap toward target, target decays (all lerp) ---------
        self.recoil_target = lerp(self.recoil_target, 0.0, min(1.0, dt * 10))
        self.recoil = lerp(self.recoil, self.recoil_target, min(1.0, dt * 35))
        if abs(self._pitch_pending) > 1e-3:
            step = self._pitch_pending * min(1.0, dt * 25)
            self._pitch_pending -= step
            p.camera_pivot.rotation_x -= step

        if self._flash_t > 0:
            self._flash_t -= dt
            if self._flash_t <= 0:
                self.flash.enabled = False

        # ---- sway from mouse movement ------------------------------------
        mv = mouse.velocity if mouse.locked else Vec3(0, 0, 0)
        sway_scale = 0.15 if self.is_scoped else 1.5
        sway_target = Vec3(clamp(-mv[0] * sway_scale, -0.06, 0.06), clamp(-mv[1] * sway_scale, -0.06, 0.06), 0)
        self.sway = lerp(self.sway, sway_target, min(1.0, dt * 10))

        # ---- walk bob + breathing ----------------------------------------
        walking = p.moving and p.grounded
        self.bob_amount = lerp(self.bob_amount, 1.0 if walking else 0.0, min(1.0, dt * 8))
        self.bob_phase += dt * (14 if p.sprinting else 9)
        bob = Vec3(sin(self.bob_phase) * 0.012, -abs(sin(self.bob_phase)) * 0.016, 0) * self.bob_amount
        breathe = sin(time.time() * 1.6) * 0.002

        self.sprint_blend = lerp(self.sprint_blend, 1.0 if p.sprinting else 0.0, min(1.0, dt * 8))
        sb = self.sprint_blend

        dip = 0.0
        if self.reloading:
            dip = sin((1.0 - self.reload_timer / max(0.01, self.stats["reload"])) * pi)

        self.position = (Weapon.BASE_POS + self.sway + bob
                         + Vec3(-sb * 0.05, breathe - dip * 0.22 - sb * 0.05, -self.recoil * 0.09))
        self.rotation = Vec3(-self.recoil * 6 + dip * 40 + sb * 8,
                             -self.sway.x * 40 - sb * 20,
                             -self.sway.x * 60)
