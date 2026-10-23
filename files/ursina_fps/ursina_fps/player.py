"""Player: FirstPersonController + sprint, FOV kick, health and regeneration."""
from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController

import config


class Player(FirstPersonController):
    def __init__(self, game):
        super().__init__(
            position=Vec3(0, 0, 0),
            speed=config.WALK_SPEED,
            jump_height=config.JUMP_HEIGHT,
            mouse_sensitivity=Vec2(*config.MOUSE_SENSITIVITY),
        )
        self.game = game
        self.cursor.enabled = False            # we draw our own dynamic crosshair
        self.health = float(config.PLAYER_MAX_HEALTH)
        self.max_health = float(config.PLAYER_MAX_HEALTH)
        self.moving = False
        self.sprinting = False
        self.since_hit = 999.0

    # -------------------------------------------------------------- update
    def update(self):
        dt = time.dt
        self.moving = bool(held_keys["w"] or held_keys["a"] or held_keys["s"] or held_keys["d"])
        self.sprinting = bool(held_keys["left shift"] and held_keys["w"])
        self.speed = config.SPRINT_SPEED if self.sprinting else config.WALK_SPEED

        target_fov = config.SPRINT_FOV if self.sprinting else config.BASE_FOV
        camera.fov = lerp(camera.fov, target_fov, min(1.0, dt * 8))

        super().update()                       # mouse look (pitch clamped), WASD, gravity, jump

        self.since_hit += dt
        if self.since_hit > config.REGEN_DELAY and self.health < self.max_health:
            self.health = min(self.max_health, self.health + config.REGEN_RATE * dt)

    # -------------------------------------------------------------- health
    def take_damage(self, amount):
        if self.game.state != "playing":
            return
        self.health = max(0.0, self.health - amount)
        self.since_hit = 0.0
        self.game.hud.damage_flash(min(1.0, 0.35 + amount / 30))
        self.game.audio.play("player_hurt")
        if self.health <= 0:
            self.game.finish(win=False)

    def heal(self, amount):
        self.health = min(self.max_health, self.health + amount)

    def reset(self):
        self.position = Vec3(0, 0, 0)
        self.rotation_y = 0
        self.camera_pivot.rotation_x = 0
        self.health = self.max_health
        self.since_hit = 999.0
        self.air_time = 0
        camera.fov = config.BASE_FOV
