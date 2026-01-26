import pygame
from core.settings import ENEMY_RADIUS, ENEMY_COLOR, ENEMY_MAX_HP, ENEMY_SPEED

class Enemy:
    def __init__(self, pos):
        self.pos = pygame.Vector2(pos)
        self.hp = 60  # lowered from 60 to 40
        self.alive = True
        self.hit_flash = 0.0  # timer for hit feedback

    def update(self, dt, player_pos):
        if not self.alive:
            return

        # Reduce hit flash timer
        self.hit_flash = max(0, self.hit_flash - dt)

        # Simple AI: move toward player
        to_player = player_pos - self.pos
        if to_player.length_squared() > 0:
            self.pos += to_player.normalize() * ENEMY_SPEED * dt

    def take_damage(self, dmg):
        self.hp -= dmg
        self.hit_flash = 0.08  # flash white for 0.08 sec
        if self.hp <= 0:
            self.alive = False

    def draw(self, surface):
        if not self.alive:
            return
        color = (255, 255, 255) if self.hit_flash > 0 else ENEMY_COLOR
        pygame.draw.circle(surface, color, (int(self.pos.x), int(self.pos.y)), ENEMY_RADIUS)

        # Draw health bar
        bar_w, bar_h = 34, 6
        x = int(self.pos.x - bar_w/2)
        y = int(self.pos.y - ENEMY_RADIUS - 12)
        hp_ratio = max(0, self.hp / ENEMY_MAX_HP)
        pygame.draw.rect(surface, (60,60,70), (x,y,bar_w,bar_h))
        pygame.draw.rect(surface, (120,240,160), (x,y,int(bar_w*hp_ratio),bar_h))
