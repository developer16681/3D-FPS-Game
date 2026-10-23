"""Game: owns every subsystem, the play/dead/won state machine and restart logic."""
from ursina import *

import config
from audio_manager import AudioManager
from hud import HUD
from player import Player
from spawn_manager import SpawnManager
from vfx import VFX
from weapon import Weapon
from world import World


class Game(Entity):
    def __init__(self, app):
        super().__init__()
        self.state = "playing"            # playing | dead | won
        self.kills = 0
        self.elapsed = 0.0

        self.world = World()
        self.audio = AudioManager(app.loader)
        self.vfx = VFX()
        self.player = Player(self)
        self.weapon = Weapon(self)
        self.spawner = SpawnManager(self)
        self.hud = HUD(self)
        self.audio.on_volume_change = self.hud.toast

        self.restart()
        self.audio.start_music()

    # ---------------------------------------------------------- lifecycle
    def restart(self):
        self.state = "playing"
        self.kills = 0
        self.elapsed = 0.0
        self.player.reset()
        self.player.enabled = True
        self.weapon.reset()
        self.weapon.enabled = True
        self.spawner.reset()
        self.vfx.clear()
        self.hud.reset()
        mouse.locked = True

    def finish(self, win):
        if self.state != "playing":
            return
        self.state = "won" if win else "dead"
        self.player.enabled = False
        self.weapon.enabled = False
        mouse.locked = False
        self.hud.show_end(win)

    def on_enemy_killed(self, enemy):
        self.kills += 1

    # -------------------------------------------------------------- loop
    def update(self):
        if self.state == "playing":
            self.elapsed += time.dt

    def input(self, key):
        if key == "escape":
            application.quit()
        elif key == "r" and self.state != "playing":
            self.restart()
        elif key == "f1":
            self.audio.change_music(-0.1)
        elif key == "f2":
            self.audio.change_music(0.1)
        elif key == "f3":
            self.audio.change_sfx(-0.1)
        elif key == "f4":
            self.audio.change_sfx(0.1)
        elif key == "m":
            self.audio.toggle_mute()
