# entities/enemy.py - COMPLETE UPDATED VERSION
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
        
        # Attack cooldown to prevent per-frame damage
        self.attack_cooldown = 0
        self.attack_interval = 1.0

    def take_damage(self, dmg, source_pos=None):
        self.hp -= dmg
        self.hit_timer = 0.15

        if source_pos:
            direction = self.pos - source_pos
            if direction.length_squared() > 0:
                self.knockback = direction.normalize() * 180

        if self.hp <= 0:
            self.alive = False
            return True
        return False

    def update(self, player, dt, walls):
        if not self.alive:
            return

        # Update attack cooldown
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt

        # Hit flash timer
        if self.hit_timer > 0:
            self.hit_timer -= dt

        # Knockback decay
        if self.knockback.length_squared() > 0:
            self.pos += self.knockback * dt
            self.knockback *= 0.85

        # Check player's melee attack
        if hasattr(player, 'melee_attack') and player.melee_attack and player.melee_attack.active:
            melee_distance = (self.pos - player.melee_attack.pos).length()
            if melee_distance < self.radius + player.melee_attack.radius:
                died = self.take_damage(player.melee_attack.damage, player.melee_attack.pos)
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

            for wall in walls:
                if rect.colliderect(wall):
                    self.pos = old_pos
                    break

            # Keep enemy in room bounds
            screen_width, screen_height = pygame.display.get_surface().get_size()
            self.pos.x = max(self.radius, min(self.pos.x, screen_width - self.radius))
            self.pos.y = max(self.radius, min(self.pos.y, screen_height - self.radius))

        # Damage player on contact
        if (player.pos - self.pos).length() < self.radius + 14 and self.attack_cooldown <= 0:
            player.take_damage(self.damage)
            self.attack_cooldown = self.attack_interval

    def draw(self, screen, camera):
        if not self.alive:
            return

        screen_pos = camera.apply_pos(self.pos)
        
        if self.enemy_type == "boss":
            color = (255, 50, 50) if self.hit_timer > 0 else (200, 30, 30)
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
        self.target = None

    def update(self, player, dt):
        if not self.active:
            return False
        
        self.timer += dt
        
        # Bobbing animation
        bob_y = math.sin(self.timer * 3.5) * 3
        
        # If player is close, start collecting immediately
        if (player.pos - self.pos).length() < 80:
            self.target = player.pos.copy()
        
        if self.target:
            # Move toward player with increasing speed
            direction = self.target - self.pos
            if direction.length_squared() > 0:
                distance = direction.length()
                # Speed increases as it gets closer to player
                speed = min(800, 200 + (100 - distance) * 10)
                self.pos += direction.normalize() * speed * dt
            
            # Check if reached player
            if (player.pos - self.pos).length() < 15:
                self.active = False
                return True
        
        # Apply bobbing
        self.pos.y += bob_y * dt
        return False

    def draw(self, screen, camera):
        if not self.active:
            return
        
        screen_pos = camera.apply_pos(self.pos)
        
        # Add bobbing to the position
        bob_y = math.sin(self.timer * 3.5) * 5
        draw_y = screen_pos.y + bob_y
        
        # XP orb
        radius = 8
        pygame.draw.circle(screen, (100, 255, 100), (int(screen_pos.x), int(draw_y)), radius)
        pygame.draw.circle(screen, (150, 255, 150), (int(screen_pos.x), int(draw_y)), radius - 2)
        
        # Add a pulsing glow effect
        pulse = math.sin(self.timer * 5) * 2 + 2
        glow_surface = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
        pygame.draw.circle(glow_surface, (100, 255, 100, 80), 
                          (radius * 2, radius * 2), 
                          int(radius + pulse))
        screen.blit(glow_surface, (screen_pos.x - radius * 2, draw_y - radius * 2))
        
        # XP amount text
        font = pygame.font.Font(None, 20)
        text = font.render(str(self.amount), True, (255, 255, 255))
        screen.blit(text, (screen_pos.x - text.get_width()//2, draw_y - radius - 15))


class ShardPickup:
    def __init__(self, pos, amount):
        self.pos = pygame.Vector2(pos)
        self.amount = amount
        self.active = True
        self.timer = 0
        self.target = None

    def update(self, player, dt):
        if not self.active:
            return False
        
        self.timer += dt
        
        # Bobbing animation
        bob_y = math.sin(self.timer * 3.5) * 3
        
        # If player is close, start collecting immediately
        if (player.pos - self.pos).length() < 90:
            self.target = player.pos.copy()
        
        if self.target:
            # Move toward player
            direction = self.target - self.pos
            if direction.length_squared() > 0:
                distance = direction.length()
                speed = min(700, 150 + (100 - distance) * 8)
                self.pos += direction.normalize() * speed * dt
            
            # Check if reached player
            if (player.pos - self.pos).length() < 15:
                self.active = False
                return True
        
        self.pos.y += bob_y * dt
        return False

    def draw(self, screen, camera):
        if not self.active:
            return
        
        screen_pos = camera.apply_pos(self.pos)
        
        # Add bobbing to the position
        bob_y = math.sin(self.timer * 3.5) * 5
        draw_y = screen_pos.y + bob_y
        
        # Shard - diamond shape
        size = 14
        points = [
            (screen_pos.x, draw_y - size),
            (screen_pos.x + size, draw_y),
            (screen_pos.x, draw_y + size),
            (screen_pos.x - size, draw_y)
        ]
        
        pygame.draw.polygon(screen, (255, 215, 0), points)
        pygame.draw.polygon(screen, (255, 255, 150), points, 2)
        
        # Add inner sparkle effect
        inner_points = [
            (screen_pos.x, draw_y - size // 2),
            (screen_pos.x + size // 2, draw_y),
            (screen_pos.x - size // 2, draw_y)
        ]
        pygame.draw.polygon(screen, (255, 255, 200), inner_points)
        
        # Add glow effect
        pulse = math.sin(self.timer * 6) * 2 + 2
        glow_surface = pygame.Surface((size * 3, size * 3), pygame.SRCALPHA)
        
        # Create diamond glow
        glow_points = [
            (size * 1.5, size * 1.5 - size - pulse),
            (size * 1.5 + size + pulse, size * 1.5),
            (size * 1.5, size * 1.5 + size + pulse),
            (size * 1.5 - size - pulse, size * 1.5)
        ]
        pygame.draw.polygon(glow_surface, (255, 215, 0, 60), glow_points)
        screen.blit(glow_surface, (screen_pos.x - size * 1.5, draw_y - size * 1.5))
        
        # Shard amount text
        font = pygame.font.Font(None, 20)
        text = font.render(str(self.amount), True, (255, 255, 255))
        screen.blit(text, (screen_pos.x - text.get_width()//2, draw_y - size - 20))