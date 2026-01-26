import pygame
from core.settings import BULLET_RADIUS, WIDTH, HEIGHT

class Bullet:
    def __init__(self, pos, vel, damage, lifetime):
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(vel)
        self.damage = damage
        self.lifetime = lifetime
        self.age = 0
        self.alive = True

    def update(self, dt):
        if not self.alive: return
        self.age += dt
        if self.age >= self.lifetime: self.alive = False
        self.pos += self.vel * dt
        if (self.pos.x < -50 or self.pos.x > WIDTH + 50 or
            self.pos.y < -50 or self.pos.y > HEIGHT + 50):
            self.alive = False

    def draw(self, surface):
        pygame.draw.circle(surface, (255,230,120), self.pos, BULLET_RADIUS)
