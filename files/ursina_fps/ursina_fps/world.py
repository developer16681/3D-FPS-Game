"""Static level geometry: ground, boundary walls, cover obstacles, sky and fog."""
import random

from ursina import *

import config


class World:
    def __init__(self):
        size = config.ARENA_SIZE
        self.half = size / 2
        self.blockers = []          # (x, z, half_w, half_d) for spawn-point checks
        rng = random.Random(config.WORLD_SEED)

        Sky()
        try:
            scene.fog_color = color.hsv(215, 0.15, 0.75)
            scene.fog_density = (35, 120)
        except Exception:                                     # noqa: BLE001
            pass

        Entity(model="cube", scale=(size, 1, size), y=-0.5, texture="white_cube",
               texture_scale=(size / 2, size / 2), color=color.hsv(100, 0.15, 0.45),
               collider="box")

        wall_color = color.hsv(220, 0.08, 0.35)
        t = 2
        h = config.WALL_HEIGHT
        for pos, scl in (
            ((0, h / 2, self.half + t / 2), (size + 2 * t, h, t)),
            ((0, h / 2, -self.half - t / 2), (size + 2 * t, h, t)),
            ((self.half + t / 2, h / 2, 0), (t, h, size)),
            ((-self.half - t / 2, h / 2, 0), (t, h, size)),
        ):
            Entity(model="cube", position=pos, scale=scl, texture="white_cube",
                   texture_scale=(scl[0] / 2, scl[1] / 2), color=wall_color, collider="box")

        placed = 0
        attempts = 0
        while placed < config.OBSTACLE_COUNT and attempts < 400:
            attempts += 1
            x = rng.uniform(-self.half + 7, self.half - 7)
            z = rng.uniform(-self.half + 7, self.half - 7)
            if abs(x) < 8 and abs(z) < 8:          # keep player spawn area clear
                continue
            w, d, hh = rng.uniform(2, 5), rng.uniform(2, 5), rng.uniform(1.6, 4.0)
            if not self.point_free(x, z, max(w, d)):
                continue
            Entity(model="cube", position=(x, hh / 2, z), scale=(w, hh, d),
                   texture="white_cube", texture_scale=(w, hh),
                   color=color.hsv(rng.choice((25, 30, 200, 210)), 0.2, rng.uniform(0.35, 0.55)),
                   collider="box")
            self.blockers.append((x, z, w / 2, d / 2))
            placed += 1

    def point_free(self, x, z, pad=1.0):
        for bx, bz, hw, hd in self.blockers:
            if abs(x - bx) < hw + pad and abs(z - bz) < hd + pad:
                return False
        return True
