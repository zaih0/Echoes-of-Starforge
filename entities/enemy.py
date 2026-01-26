import pygame
from core.settings import *

class Enemy:
    def __init__(self, pos):
        self.pos = pygame.Vector2(pos)
        self.hp = ENEMY_MAX_HP
        self.alive = True

    def update(self, dt, player_pos):
        direction = player_pos - self.pos
        if direction.length_squared() > 0:
            self.pos += direction.normalize() * ENEMY_SPEED * dt

    def take_damage(self, dmg):
        self.hp -= dmg
        if self.hp <= 0:
            self.alive = False

    def draw(self, screen):
        pygame.draw.circle(screen, ENEMY_COLOR, self.pos, ENEMY_RADIUS)
        # health bar
        w = 30
        pct = max(0, self.hp / ENEMY_MAX_HP)
        pygame.draw.rect(screen, (60,60,60), (self.pos.x-w//2, self.pos.y-26, w, 5))
        pygame.draw.rect(screen, (120,240,160), (self.pos.x-w//2, self.pos.y-26, w*pct, 5))
