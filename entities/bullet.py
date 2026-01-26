import pygame
from core.settings import *

class Bullet:
    def __init__(self, pos, vel, damage):
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(vel)
        self.damage = damage
        self.alive = True

    def update(self, dt):
        self.pos += self.vel * dt
        if self.pos.x < -50 or self.pos.x > WIDTH+50 or \
           self.pos.y < -50 or self.pos.y > HEIGHT+50:
            self.alive = False

    def draw(self, screen):
        pygame.draw.circle(screen, BULLET_COLOR, self.pos, BULLET_RADIUS)
