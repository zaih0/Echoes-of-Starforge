# entities/bullet.py
import pygame
from core.settings import *

class Bullet:
    def __init__(self, pos, vel, damage):
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(vel)
        self.damage = damage
        self.alive = True
        self.radius = BULLET_RADIUS

    def update(self, dt):
        self.pos += self.vel * dt
        # Bullets die when they hit walls or go off screen
        if (self.pos.x < 0 or self.pos.x > WIDTH or 
            self.pos.y < 0 or self.pos.y > HEIGHT):
            self.alive = False

    def draw_at_position(self, screen, screen_pos):
        # screen_pos can be either a tuple or Vector2
        if hasattr(screen_pos, 'x'):
            # It's a Vector2
            x, y = screen_pos.x, screen_pos.y
        else:
            # It's a tuple
            x, y = screen_pos
        
        pygame.draw.circle(screen, (255, 230, 120), (int(x), int(y)), self.radius)