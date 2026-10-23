"""Weapon: viewmodel parented to the camera, sway/bob/recoil, hitscan raycast, ammo & reload."""
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
        self._build_model()

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
        self.reset()

    # --------------------------------------------------------------- model
    def _build_model(self):
        dark = color.hsv(220, 0.10, 0.18)
        mid = color.hsv(220, 0.08, 0.32)
        accent = color.hsv(30, 0.7, 0.6)
        Entity(parent=self, model="cube", scale=(0.085, 0.11, 0.42), position=(0, 0, 0.05), color=dark)
        Entity(parent=self, model="cube", scale=(0.07, 0.05, 0.38), position=(0, 0.075, 0.07), color=mid)
        Entity(parent=self, model="cube", scale=(0.035, 0.035, 0.30), position=(0, 0.015, 0.38), color=dark)
        Entity(parent=self, model="cube", scale=(0.07, 0.17, 0.07), position=(0, -0.12, -0.07),
               rotation_x=-15, color=mid)
        Entity(parent=self, model="cube", scale=(0.06, 0.14, 0.08), position=(0, -0.11, 0.12), color=dark)
        Entity(parent=self, model="cube", scale=(0.012, 0.025, 0.012), position=(0, 0.11, 0.2), color=accent)

        self.muzzle = Entity(parent=self, position=(0, 0.015, 0.56))
        self.flash = Entity(parent=self.muzzle, enabled=False)
        Entity(parent=self.flash, model="sphere", scale=0.1, color=color.yellow)
        Entity(parent=self.flash, model="quad", scale=0.32, color=color.orange)
        Entity(parent=self.flash, model="quad", scale=0.32, rotation_z=45, z=0.01, color=color.yellow)

    # --------------------------------------------------------------- state
    def reset(self):
        self.mag = config.MAG_SIZE
        self.reserve = config.START_RESERVE
        self.cooldown = 0.0
        self.reloading = False
        self.reload_timer = 0.0
        self.recoil = self.recoil_target = self.fire_kick = self.spread = 0.0
        self._pitch_pending = 0.0
        self._flash_t = 0.0
        self.flash.enabled = False
        self.position = Weapon.BASE_POS
        self.rotation = Vec3(0, 0, 0)

    def add_reserve(self, amount):
        self.reserve = min(config.MAX_RESERVE, self.reserve + amount)

    # --------------------------------------------------------------- input
    def input(self, key):
        if key == "left mouse down":
            self._trigger_pressed = True
        elif key == "r":
            self.start_reload()

    def start_reload(self):
        if self.reloading or self.mag >= config.MAG_SIZE or self.reserve <= 0:
            return
        self.reloading = True
        self.reload_timer = config.RELOAD_TIME
        self.game.audio.play("reload")

    def _finish_reload(self):
        take = min(config.MAG_SIZE - self.mag, self.reserve)
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
        self.cooldown = config.FIRE_INTERVAL
        self.recoil_target = 1.0
        self.fire_kick = min(0.6, self.fire_kick + 0.18)
        self._pitch_pending += random.uniform(0.5, 0.9)      # camera climbs smoothly
        p.rotation_y += random.uniform(-0.2, 0.2)
        self._flash_t = 0.04
        self.flash.enabled = True
        self.flash.scale = random.uniform(0.8, 1.3)
        self.flash.rotation_z = random.uniform(0, 360)
        self.game.audio.play("gunshot")
        self._shoot_ray()

    def _shoot_ray(self):
        game = self.game
        jitter = self.spread * 0.035
        direction = (camera.forward
                     + camera.right * random.uniform(-jitter, jitter)
                     + camera.up * random.uniform(-jitter, jitter)).normalized()
        origin = camera.world_position
        hit = raycast(origin, direction, distance=config.MAX_RANGE, ignore=[game.player], debug=False)

        end = hit.world_point if hit.hit else origin + direction * 80
        game.vfx.tracer(self.muzzle.world_position, end)
        if not hit.hit:
            return

        ent = hit.entity
        if isinstance(ent, Enemy) and ent.alive:
            head = (hit.world_point.y - ent.y) / ent.scale_y >= config.HEAD_HEIGHT
            dmg = config.DAMAGE * (config.HEADSHOT_MULT if head else 1.0)
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

        if self.reloading:
            self.reload_timer -= dt
            if self.reload_timer <= 0:
                self._finish_reload()

        held = bool(held_keys["left mouse"]) and mouse.locked
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
        sway_target = Vec3(clamp(-mv[0] * 1.5, -0.06, 0.06), clamp(-mv[1] * 1.5, -0.06, 0.06), 0)
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
            dip = sin((1.0 - self.reload_timer / config.RELOAD_TIME) * pi)

        self.position = (Weapon.BASE_POS + self.sway + bob
                         + Vec3(-sb * 0.05, breathe - dip * 0.22 - sb * 0.05, -self.recoil * 0.09))
        self.rotation = Vec3(-self.recoil * 6 + dip * 40 + sb * 8,
                             -self.sway.x * 40 - sb * 20,
                             -self.sway.x * 60)
