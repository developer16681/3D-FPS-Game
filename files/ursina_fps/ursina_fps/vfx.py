"""Pooled visual effects: impact/blood particles, bullet tracers, bullet-hole decals.

Everything is pre-allocated once and recycled, so firing never creates garbage
entities (keeps the frame-rate stable during full-auto fire).
"""
import random

from ursina import *

import config


class _Particle:
    __slots__ = ("entity", "vel", "life", "max_life", "size")

    def __init__(self):
        self.entity = Entity(model="cube", scale=0.05, enabled=False)
        self.vel = Vec3(0, 0, 0)
        self.life = 0.0
        self.max_life = 1.0
        self.size = 0.05


class VFX(Entity):
    def __init__(self):
        super().__init__()
        self._particles = [_Particle() for _ in range(config.PARTICLE_POOL)]
        self._p_i = 0

        self._tracers = []     # [entity, life]
        for _ in range(config.TRACER_POOL):
            e = Entity(model="cube", color=color.hsv(50, 0.5, 1), enabled=False)
            self._tracers.append([e, 0.0])
        self._t_i = 0

        self._decals = []
        for _ in range(config.DECAL_POOL):
            self._decals.append(Entity(model="quad", color=color.hsv(0, 0, 0.05),
                                       scale=0.14, enabled=False))
        self._d_i = 0

    # ------------------------------------------------------------ spawning
    def burst(self, point, normal, col=None, count=8, speed=4.0, size=0.055):
        col = col or color.hsv(40, 0.3, 0.9)
        for _ in range(count):
            p = self._particles[self._p_i]
            self._p_i = (self._p_i + 1) % len(self._particles)
            jitter = Vec3(random.uniform(-1, 1), random.uniform(0.0, 1.2), random.uniform(-1, 1))
            p.vel = normal * speed * random.uniform(0.3, 1.0) + jitter * speed * 0.5
            p.life = p.max_life = random.uniform(0.25, 0.5)
            p.size = size * random.uniform(0.7, 1.3)
            e = p.entity
            e.position = point
            e.scale = p.size
            e.color = col
            e.enabled = True

    def impact(self, point, normal):
        self.burst(point, normal, col=color.hsv(35, 0.25, 0.85), count=7, speed=3.5)

    def blood(self, point, normal):
        self.burst(point, normal, col=color.hsv(0, 0.9, 0.7), count=9, speed=3.0, size=0.06)

    def tracer(self, start, end):
        d = end - start
        dist = d.length()
        if dist < 0.5:
            return
        slot = self._tracers[self._t_i]
        self._t_i = (self._t_i + 1) % len(self._tracers)
        e = slot[0]
        e.position = (start + end) / 2
        e.look_at(end)
        e.scale = Vec3(0.015, 0.015, dist)
        e.enabled = True
        slot[1] = 0.05

    def decal(self, point, normal):
        e = self._decals[self._d_i]
        self._d_i = (self._d_i + 1) % len(self._decals)
        e.position = point + normal * 0.02
        e.look_at(e.position - normal)     # quad's visible side faces -Z
        e.rotation_z = random.uniform(0, 360)
        e.enabled = True

    def clear(self):
        for p in self._particles:
            p.life = 0.0
            p.entity.enabled = False
        for slot in self._tracers:
            slot[1] = 0.0
            slot[0].enabled = False
        for d in self._decals:
            d.enabled = False

    # -------------------------------------------------------------- update
    def update(self):
        dt = time.dt
        for p in self._particles:
            if p.life <= 0.0:
                continue
            p.life -= dt
            if p.life <= 0.0:
                p.entity.enabled = False
                continue
            p.vel.y -= 9.0 * dt
            p.entity.position += p.vel * dt
            p.entity.scale = p.size * (p.life / p.max_life)
        for slot in self._tracers:
            if slot[1] > 0.0:
                slot[1] -= dt
                if slot[1] <= 0.0:
                    slot[0].enabled = False
