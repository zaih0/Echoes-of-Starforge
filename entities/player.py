# entities/player.py
import pygame
import random
import math
from core.settings import PLAYER_RADIUS, PLAYER_SPEED, PLAYER_MAX_HP
from entities.melee import SwordArc

class Player:
    def __init__(self, x, y, skill_bonuses=None):
        self.pos = pygame.Vector2(x, y)
        self.base_speed = PLAYER_SPEED
        self.speed = PLAYER_SPEED
        
        self.base_max_hp = PLAYER_MAX_HP
        self.max_hp = PLAYER_MAX_HP
        self.hp = PLAYER_MAX_HP

        self.weapon = None
        self.skill_bonuses = skill_bonuses or {}
        
        # Apply skill tree bonuses
        self._apply_skill_bonuses()
        
        # Temporary level-up bonuses
        self.damage_multiplier = 1.0
        self.fire_rate_multiplier = 1.0
        self.crit_chance = 0.0
        self.life_steal = 0.0
        self.health_regen = 0.0
        self.damage_reduction = 0.0
        self.multi_shot = 1
        self.bullet_speed_multiplier = 1.0
        
        # Timers
        self.shoot_timer = 0
        self.shoot_flash_timer = 0
        self.sword_swing_timer = 0
        self.melee_cooldown = 0
        self.regen_timer = 0
        self.facing = pygame.Vector2(1, 0)  # Start facing right
        
        # Visual effects
        self.hit_flash_timer = 0
        self.level_up_effect_timer = 0

    def _apply_skill_bonuses(self):
        """Apply permanent skill tree bonuses"""
        bonuses = self.skill_bonuses
        
        # Health bonus
        if "health" in bonuses:
            self.max_hp = self.base_max_hp + (bonuses["health"] * 20)
            self.hp = self.max_hp
        
        # Speed bonus
        if "speed" in bonuses:
            self.speed = self.base_speed * (1 + bonuses["speed"] * 0.05)

    def take_damage(self, dmg):
        """Take damage with damage reduction"""
        actual_damage = dmg * (1 - self.damage_reduction)
        self.hp -= actual_damage
        self.hit_flash_timer = 0.2
        
        if self.hp < 0:
            self.hp = 0
        return actual_damage

    def heal(self, amount):
        """Heal the player"""
        self.hp = min(self.max_hp, self.hp + amount)

    def update(self, dt, bullets, keys, mouse_pos, mouse_pressed, room, camera):
        # Movement input
        move = pygame.Vector2(0, 0)
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            move.y -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            move.y += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            move.x -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            move.x += 1
        
        # Normalize diagonal movement
        if move.length_squared() > 0:
            move = move.normalize()
            self.pos += move * self.speed * dt
        
        # Update facing direction based on mouse
        if mouse_pos:
            # Convert screen mouse position to world position
            world_mouse_pos = pygame.Vector2(
                mouse_pos[0] + camera.camera.x,
                mouse_pos[1] + camera.camera.y
            )
            direction = world_mouse_pos - self.pos
            if direction.length_squared() > 0:
                self.facing = direction.normalize()

        # Update timers
        if self.shoot_timer > 0:
            self.shoot_timer -= dt
        if self.shoot_flash_timer > 0:
            self.shoot_flash_timer -= dt
        if self.sword_swing_timer > 0:
            self.sword_swing_timer -= dt
        if self.melee_cooldown > 0:
            self.melee_cooldown -= dt
        if self.hit_flash_timer > 0:
            self.hit_flash_timer -= dt
        if self.level_up_effect_timer > 0:
            self.level_up_effect_timer -= dt
        if self.regen_timer > 0:
            self.regen_timer -= dt
        
        # Health regeneration
        if self.health_regen > 0 and self.regen_timer <= 0:
            self.heal(self.health_regen * dt)
            self.regen_timer = 1.0
        
        # Shooting with mouse
        if self.weapon and mouse_pressed[0]:  # Left mouse button
            if self.shoot_timer <= 0:
                fire_rate = self.weapon.fire_rate * self.fire_rate_multiplier
                
                # Apply skill tree reload bonus
                if "reload" in self.skill_bonuses:
                    fire_rate *= (1 + self.skill_bonuses["reload"] * 0.15)
                
                # Multi-shot
                for i in range(self.multi_shot):
                    if self.multi_shot > 1:
                        # Spread out multiple shots
                        angle_offset = (i - (self.multi_shot - 1) / 2) * 0.1
                        direction = self.facing.rotate(angle_offset * 30)
                    else:
                        direction = self.facing
                    
                    # Fire bullet from player position (in world coordinates)
                    bullet = self.weapon.fire(self.pos + direction * (PLAYER_RADIUS + 20), direction)
                    if bullet:
                        # Apply bullet speed multiplier
                        bullet.vel *= self.bullet_speed_multiplier
                        
                        # Apply damage multiplier
                        damage_mult = self.damage_multiplier
                        if "damage" in self.skill_bonuses:
                            damage_mult *= (1 + self.skill_bonuses["damage"] * 0.1)
                        
                        # Critical strike chance
                        if random.random() < self.crit_chance:
                            damage_mult *= 2.0  # Double damage on crit
                        
                        bullet.damage *= damage_mult
                        bullets.append(bullet)
                
                self.shoot_timer = 1 / fire_rate
                self.shoot_flash_timer = 0.08

        # Melee attack with right mouse button
        if mouse_pressed[2] and self.melee_cooldown <= 0:  # Right mouse button
            self.sword_swing_timer = 0.15
            # Create melee attack at player position (world coordinates)
            room.melees.append(SwordArc(self.pos.copy(), self.facing))
            self.melee_cooldown = 0.4

        # Keep player in room bounds
        if room:
            room.keep_player_in_bounds(self)

    def draw(self, screen, camera):
        # Get screen position using camera
        screen_pos = camera.apply(self)
        
        # Draw player body with hit flash
        if self.hit_flash_timer > 0:
            color = (255, 100, 100)  # Red when hit
        elif self.level_up_effect_timer > 0:
            # Pulsing effect when leveling up
            pulse = (pygame.time.get_ticks() % 1000) / 1000
            brightness = 150 + int(105 * abs(pulse - 0.5) * 2)
            color = (brightness, brightness, 255)
        else:
            color = (80, 200, 255)
        
        pygame.draw.circle(screen, color, (int(screen_pos.x), int(screen_pos.y)), PLAYER_RADIUS)
        
        # Draw facing indicator
        facing_end = screen_pos + self.facing * (PLAYER_RADIUS + 8)
        pygame.draw.line(screen, (255, 255, 255), screen_pos, facing_end, 2)

        # Muzzle flash
        if self.shoot_flash_timer > 0:
            flash_pos = screen_pos + self.facing * (PLAYER_RADIUS + 20)
            pygame.draw.circle(screen, (255, 220, 120), (int(flash_pos.x), int(flash_pos.y)), 10)

        # Health bar
        self._draw_health_bar(screen, screen_pos)
        
        # Level up effect particles
        if self.level_up_effect_timer > 0:
            self._draw_level_up_effect(screen, screen_pos)

    def _draw_health_bar(self, screen, screen_pos):
        bar_w = 80
        bar_h = 10
        ratio = self.hp / self.max_hp
        
        # Background
        bar_rect = pygame.Rect(
            screen_pos.x - bar_w//2,
            screen_pos.y - PLAYER_RADIUS - 25,
            bar_w,
            bar_h
        )
        pygame.draw.rect(screen, (40, 40, 40), bar_rect)
        
        # Health fill
        fill_color = (220, 60, 60)  # Red when low health
        if ratio > 0.5:
            fill_color = (60, 220, 60)  # Green when healthy
        elif ratio > 0.25:
            fill_color = (220, 220, 60)  # Yellow when medium
        
        pygame.draw.rect(screen, fill_color, 
                        (bar_rect.x, bar_rect.y, bar_w * ratio, bar_h))

    def _draw_level_up_effect(self, screen, screen_pos):
        """Draw particle effect for level up"""
        for i in range(8):
            angle = (pygame.time.get_ticks() / 100 + i * 45) * 0.0174533
            radius = 20 + (pygame.time.get_ticks() % 1000) / 1000 * 10
            x = screen_pos.x + math.cos(angle) * radius
            y = screen_pos.y + math.sin(angle) * radius
            
            color = (255, 215, 0)  # Gold color
            pygame.draw.circle(screen, color, (int(x), int(y)), 3)