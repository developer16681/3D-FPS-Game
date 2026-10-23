"""Screen-space HUD: dynamic crosshair, hit marker, ammo, health, kills, wave, banners, end screen."""
import math

from ursina import *

import config


class HUD(Entity):
    def __init__(self, game):
        super().__init__(parent=camera.ui)
        self.game = game
        ar = window.aspect_ratio
        L, R, T, B = -ar / 2, ar / 2, 0.5, -0.5

        # damage / low-health vignette (behind everything)
        self.overlay = Entity(parent=self, model="quad", scale=(ar * 1.2, 1.2), z=2,
                              color=color.hsv(0, 0.9, 0.9, 0.0))
        self._dmg = 0.0

        # crosshair: left, right, top, bottom + centre dot
        self.gap = 0.012
        self._ch = [
            Entity(parent=self, model="quad", color=color.white, scale=(0.016, 0.004)),
            Entity(parent=self, model="quad", color=color.white, scale=(0.016, 0.004)),
            Entity(parent=self, model="quad", color=color.white, scale=(0.004, 0.016)),
            Entity(parent=self, model="quad", color=color.white, scale=(0.004, 0.016)),
        ]
        Entity(parent=self, model="quad", color=color.white, scale=0.004)

        # hit marker (two crossed ticks)
        self.marker = Entity(parent=self, enabled=False, z=-1)
        Entity(parent=self.marker, model="quad", scale=(0.045, 0.005), rotation_z=45)
        Entity(parent=self.marker, model="quad", scale=(0.045, 0.005), rotation_z=-45)
        self._marker_t = 0.0

        # text elements
        self.ammo_text = self._text("", R - 0.04, B + 0.07, 2.2, (0.5, 0))
        self.reload_text = self._text("RELOADING...", 0, -0.09, 1.3, (0, 0), color.yellow)
        self.reload_text.enabled = False
        self.kills_text = self._text("KILLS 0", R - 0.04, T - 0.04, 1.5, (0.5, 0))
        self.wave_text = self._text("", 0, T - 0.04, 1.6, (0, 0))
        self.time_text = self._text("00:00", L + 0.04, T - 0.04, 1.5, (-0.5, 0))
        self.hp_label = self._text("", L + 0.04, B + 0.105, 1.2, (-0.5, 0))
        self.banner_text = self._text("", 0, 0.22, 3, (0, 0), color.yellow, z=-1)
        self.banner_text.enabled = False
        self._banner_t = 0.0
        self.toast_text = self._text("", 0, B + 0.2, 1.1, (0, 0), color.light_gray)
        self._toast_t = 0.0
        self.hint_text = self._text(
            "WASD move | Shift sprint | Space jump | LMB fire | R reload | F1-F4 volume | M mute | Esc quit",
            0, -0.4, 0.9, (0, 0), color.light_gray)
        self._hint_t = 9.0

        # health bar
        self.bar_w = 0.42
        Entity(parent=self, model="quad", color=color.hsv(0, 0, 0.1, 0.8),
               origin=(-0.5, 0), position=(L + 0.04, B + 0.06, 0.01), scale=(self.bar_w + 0.01, 0.036))
        self.hp_fill = Entity(parent=self, model="quad", origin=(-0.5, 0), color=color.lime,
                              position=(L + 0.045, B + 0.06, 0), scale=(self.bar_w, 0.028))

        # end-of-game panel
        self.end_panel = Entity(parent=self, enabled=False, z=-5)
        Entity(parent=self.end_panel, model="quad", scale=(ar * 1.2, 1.2), color=color.hsv(0, 0, 0, 0.75))
        self.end_title = self._text("", 0, 0.2, 4, (0, 0), parent=self.end_panel, z=-1)
        self.end_stats = self._text("", 0, 0.06, 1.8, (0, 0), parent=self.end_panel, z=-1)
        self._text("Press R to restart", 0, -0.04, 1.4, (0, 0), color.light_gray,
                   parent=self.end_panel, z=-1)
        Button(parent=self.end_panel, text="RESTART (R)", scale=(0.3, 0.08), y=-0.16, z=-1,
               on_click=self.game.restart)

    def _text(self, txt, x, y, scale, origin, col=color.white, z=0, parent=None):
        t = Text(txt, parent=parent or self, position=Vec3(x, y, z), origin=origin, scale=scale, color=col)
        return t

    # ------------------------------------------------------------ events
    def hit_marker(self, kill=False, head=False):
        col = color.red if kill else (color.orange if head else color.white)
        for c in self.marker.children:
            c.color = col
        self.marker.enabled = True
        self._marker_t = 0.14

    def damage_flash(self, strength):
        self._dmg = max(self._dmg, strength * 0.5)

    def banner(self, text, duration=2.0):
        self.banner_text.text = text
        self.banner_text.enabled = True
        self._banner_t = duration

    def toast(self, text, duration=1.5):
        self.toast_text.text = text
        self._toast_t = duration

    def set_wave(self, n):
        total = "" if config.ENDLESS else f" / {config.WAVES_TO_WIN}"
        self.wave_text.text = f"WAVE {n}{total}"

    def show_end(self, win):
        g = self.game
        self.end_title.text = "VICTORY!" if win else "YOU DIED"
        self.end_title.color = color.lime if win else color.red
        m, s = divmod(int(g.elapsed), 60)
        self.end_stats.text = f"Kills: {g.kills}     Wave: {g.spawner.wave}     Time: {m:02d}:{s:02d}"
        self.end_panel.enabled = True

    def reset(self):
        self.end_panel.enabled = False
        self.banner_text.enabled = False
        self.marker.enabled = False
        self.set_wave(0)
        self.wave_text.text = ""
        self._dmg = 0.0
        self._hint_t = 6.0
        self.hint_text.enabled = True

    # ------------------------------------------------------------ update
    def update(self):
        dt = time.dt
        g = self.game
        w, p = g.weapon, g.player

        # dynamic crosshair
        target = 0.012 + w.spread * 0.055
        self.gap = lerp(self.gap, target, min(1.0, dt * 14))
        gp = self.gap + 0.008
        self._ch[0].position = Vec3(-gp, 0, 0)
        self._ch[1].position = Vec3(gp, 0, 0)
        self._ch[2].position = Vec3(0, gp, 0)
        self._ch[3].position = Vec3(0, -gp, 0)

        # ammo
        self.ammo_text.text = f"{w.mag:02d} / {w.reserve}"
        self.ammo_text.color = color.red if w.mag <= config.MAG_SIZE * 0.2 else color.white
        self.reload_text.enabled = w.reloading

        # health
        frac = max(0.0, min(1.0, p.health / p.max_health))
        self.hp_fill.scale_x = max(0.0001, self.bar_w * frac)
        self.hp_fill.color = color.hsv(120 * frac, 0.8, 0.9)
        self.hp_label.text = f"HP {int(math.ceil(p.health))}"

        # vignette: hurt flash + pulsing when low
        self._dmg = max(0.0, self._dmg - dt * 1.6)
        low = (0.12 + 0.08 * math.sin(time.time() * 6)) if frac < 0.3 and g.state == "playing" else 0.0
        self.overlay.alpha = max(0.0, min(0.6, self._dmg + low))

        # stats
        self.kills_text.text = f"KILLS {g.kills}"
        m, s = divmod(int(g.elapsed), 60)
        self.time_text.text = f"{m:02d}:{s:02d}"

        # timers
        if self._marker_t > 0:
            self._marker_t -= dt
            if self._marker_t <= 0:
                self.marker.enabled = False
        if self._banner_t > 0:
            self._banner_t -= dt
            if self._banner_t <= 0:
                self.banner_text.enabled = False
        if self._toast_t > 0:
            self._toast_t -= dt
            if self._toast_t <= 0:
                self.toast_text.text = ""
        if self._hint_t > 0:
            self._hint_t -= dt
            if self._hint_t <= 0:
                self.hint_text.enabled = False
