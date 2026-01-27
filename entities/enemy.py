# entities/enemy.py
import pygame
import random
import math
from core.settings import ENEMY_RADIUS, ENEMY_SPEED, ENEMY_MAX_HP, ENEMY_DAMAGE, ENEMY_XP_DROP

class Enemy:
    def __init__(self, pos, enemy_type="normal"):
        self.pos = pygame.Vector2(pos)
        self.enemy_type = enemy_type
        
        if enemy_type == "boss":
            self.max_hp = 300
            self.hp = self.max_hp
            self.radius = 40
            self.speed = 100
            self.damage = 40
            self.xp_drop = 100
            self.shard_drop = 1
        else:
            self.max_hp = ENEMY_MAX_HP
            self.hp = self.max_hp
            self.radius = ENEMY_RADIUS
            self.speed = ENEMY_SPEED
            self.damage = ENEMY_DAMAGE
            self.xp_drop = ENEMY_XP_DROP
            self.shard_drop = 0
        
        self.alive = True
        self.hit_timer = 0
        self.knockback = pygame.Vector2(0, 0)

    def take_damage(self, dmg, source_pos=None):
        self.hp -= dmg
        self.hit_timer = 0.15

        if source_pos:
            direction = self.pos - source_pos
            if direction.length_squared() > 0:
                self.knockback = direction.normalize() * 180

        if self.hp <= 0:
            self.alive = False
            return True  # Enemy died
        return False  # Enemy survived

    def update(self, dt, player, room):
        if not self.alive:
            return

        # Hit flash timer
        if self.hit_timer > 0:
            self.hit_timer -= dt

        # Knockback decay
        if self.knockback.length_squared() > 0:
            self.pos += self.knockback * dt
            self.knockback *= 0.85

        # Check melee attacks
        for melee in room.melees:
            if melee.hits(self):
                if melee.damage > 0:
                    died = self.take_damage(melee.damage, melee.pos)
                    if died:
                        return

        # Chase player
        direction = player.pos - self.pos
        if direction.length_squared() > 0:
            movement = direction.normalize() * self.speed * dt
            old_pos = self.pos.copy()
            self.pos += movement

            # Check wall collision
            rect = pygame.Rect(
                self.pos.x - self.radius,
                self.pos.y - self.radius,
                self.radius * 2,
                self.radius * 2
            )

            for wall in room.wall_rects:
                if rect.colliderect(wall):
                    self.pos = old_pos
                    break

            # Keep enemy in room bounds
            self.pos.x = max(room.pixel_x + self.radius, min(self.pos.x, room.pixel_x + room.width - self.radius))
            self.pos.y = max(room.pixel_y + self.radius, min(self.pos.y, room.pixel_y + room.height - self.radius))

        # Damage player on contact
        if (player.pos - self.pos).length() < self.radius + 14:  # 14 is approximate player radius
            player.take_damage(self.damage)

    def draw(self, screen, camera):
        if not self.alive:
            return

        screen_pos = camera.apply(self)
        
        if self.enemy_type == "boss":
            color = (255, 50, 50) if self.hit_timer > 0 else (200, 30, 30)
            # Draw boss with pulsing effect
            pulse = (pygame.time.get_ticks() % 1000) / 1000
            pulse_size = self.radius + 2 * (0.5 + 0.5 * math.sin(pulse * math.pi * 2))
            pygame.draw.circle(screen, color, (int(screen_pos.x), int(screen_pos.y)), int(pulse_size))
            pygame.draw.circle(screen, (255, 100, 100), (int(screen_pos.x), int(screen_pos.y)), self.radius)
        else:
            color = (255, 80, 80) if self.hit_timer > 0 else (180, 60, 60)
            pygame.draw.circle(screen, color, (int(screen_pos.x), int(screen_pos.y)), self.radius)

        # Health bar
        ratio = max(self.hp, 0) / self.max_hp
        bar_w = 40 if self.enemy_type == "boss" else 24
        bar_h = 6 if self.enemy_type == "boss" else 4
        bar_y_offset = -self.radius - 14 if self.enemy_type == "boss" else -self.radius - 10
        
        bar_x = screen_pos.x - bar_w // 2
        bar_y = screen_pos.y + bar_y_offset
        
        pygame.draw.rect(screen, (40, 40, 40), (bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(
            screen,
            (220, 60, 60) if self.enemy_type == "normal" else (255, 50, 50),
            (bar_x, bar_y, bar_w * ratio, bar_h)
        )


class XPPickup:
    def __init__(self, pos, amount):
        self.pos = pygame.Vector2(pos)
        self.amount = amount
        self.active = True
        self.timer = 0
        self.collect_timer = 0
        self.collecting = False
        self.target = None

    def update(self, dt, player):
        if not self.active:
            return False
        
        self.timer += dt
        
        # Bobbing animation
        bob_y = math.sin(self.timer * 3.5) * 3
        
        # If player is close, start collecting
        if not self.collecting and (player.pos - self.pos).length() < 50:
            self.collecting = True
            self.collect_timer = 0.3
            self.target = player.pos.copy()
        
        if self.collecting:
            self.collect_timer -= dt
            # Move toward player
            if self.target:
                direction = self.target - self.pos
                if direction.length_squared() > 0:
                    self.pos += direction.normalize() * 400 * dt
                
                # Check if reached player
                if (player.pos - self.pos).length() < 10:
                    self.active = False
                    return True  # XP collected
        
        self.pos.y += bob_y * dt
        return False

    def draw(self, screen, camera):
        if not self.active:
            return
        
        screen_pos = camera.apply_pos(self.pos)
        
        # XP orb
        pygame.draw.circle(screen, (100, 255, 100), (int(screen_pos.x), int(screen_pos.y)), 8)
        pygame.draw.circle(screen, (150, 255, 150), (int(screen_pos.x), int(screen_pos.y)), 6)
        
        # XP amount text
        font = pygame.font.Font(None, 20)
        text = font.render(str(self.amount), True, (255, 255, 255))
        screen.blit(text, (screen_pos.x - text.get_width()//2, screen_pos.y - 20))


class ShardPickup:
    def __init__(self, pos, amount):
        self.pos = pygame.Vector2(pos)
        self.amount = amount
        self.active = True
        self.timer = 0
        self.collect_timer = 0
        self.collecting = False
        self.target = None

    def update(self, dt, player):
        if not self.active:
            return False
        
        self.timer += dt
        
        # Bobbing animation
        bob_y = math.sin(self.timer * 3.5) * 3
        
        # If player is close, start collecting
        if not self.collecting and (player.pos - self.pos).length() < 60:
            self.collecting = True
            self.collect_timer = 0.4
            self.target = player.pos.copy()
        
        if self.collecting:
            self.collect_timer -= dt
            # Move toward player
            if self.target:
                direction = self.target - self.pos
                if direction.length_squared() > 0:
                    self.pos += direction.normalize() * 350 * dt
                
                # Check if reached player
                if (player.pos - self.pos).length() < 10:
                    self.active = False
                    return True  # Shard collected
        
        self.pos.y += bob_y * dt
        return False

    def draw(self, screen, camera):
        if not self.active:
            return
        
        screen_pos = camera.apply_pos(self.pos)
        
        # Shard - draw as a diamond
        points = [
            (screen_pos.x, screen_pos.y - 10),
            (screen_pos.x + 8, screen_pos.y),
            (screen_pos.x, screen_pos.y + 10),
            (screen_pos.x - 8, screen_pos.y)
        ]
        pygame.draw.polygon(screen, (255, 215, 0), points)
        pygame.draw.polygon(screen, (255, 255, 150), points, 2)
        
        # Shard amount text
        font = pygame.font.Font(None, 20)
        text = font.render(str(self.amount), True, (255, 255, 255))
        screen.blit(text, (screen_pos.x - text.get_width()//2, screen_pos.y - 25))