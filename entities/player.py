# entities/player.py
import pygame
import random
import math
from core.settings import PLAYER_RADIUS, PLAYER_SPEED, PLAYER_MAX_HP
from entities.melee import SwordArc  # ADDED IMPORT

class Player:
    def __init__(self, x, y, skill_bonuses=None):
        self.pos = pygame.Vector2(x, y)
        self.base_speed = PLAYER_SPEED
        self.speed = PLAYER_SPEED
        
        self.base_max_hp = PLAYER_MAX_HP
        self.max_hp = PLAYER_MAX_HP
        self.hp = PLAYER_MAX_HP

        self.weapon = None
        self.charms = []  # List of active charms
        self.skill_bonuses = skill_bonuses or {}

        # Temporary level-up bonuses
        self.damage_multiplier = 1.0
        self.fire_rate_multiplier = 1.0
        self.crit_chance = 0.0
        self.life_steal = 0.0
        self.health_regen = 0.0
        self.damage_reduction = 0.0
        self.multi_shot = 1
        self.bullet_speed_multiplier = 1.0
        self.bullet_pierce = 0
        self.player_level = 1
        
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
        self.level_text_timer = 0

        # Apply skill tree bonuses (must happen after multiplier attributes are initialized)
        self._apply_skill_bonuses()

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
        
        # Apply other skill bonuses to multipliers
        if "damage" in bonuses:
            self.damage_multiplier *= (1 + bonuses["damage"] * 0.1)
        if "reload" in bonuses:
            self.fire_rate_multiplier *= (1 + bonuses["reload"] * 0.15)

    def add_charm(self, charm):
        """Add a charm to the player"""
        # Stack identical charms instead of adding duplicate list entries
        existing = next((c for c in self.charms if c.name == charm.name), None)
        if existing:
            existing.stacks = getattr(existing, "stacks", 1) + 1
            # Apply effect again for each stack
            charm.effect(self)
            print(f"Stacked charm: {charm.name} x{existing.stacks}")
        else:
            charm.stacks = 1
            self.charms.append(charm)
            charm.effect(self)
            print(f"Added charm: {charm.name} - {charm.description}")

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
            # In single-screen mode, mouse position is already in world coordinates
            direction = pygame.Vector2(mouse_pos[0], mouse_pos[1]) - self.pos
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
            self.level_text_timer = self.level_up_effect_timer
        if self.regen_timer > 0:
            self.regen_timer -= dt
        
        # Health regeneration
        if self.health_regen > 0 and self.regen_timer <= 0:
            self.heal(self.health_regen)
            self.regen_timer = 1.0
        
        # Shooting with mouse
        if self.weapon and mouse_pressed[0]:  # Left mouse button
            if self.shoot_timer <= 0:
                fire_rate = self.weapon.fire_rate * self.fire_rate_multiplier
                
                # Multi-shot
                for i in range(self.multi_shot):
                    if self.multi_shot > 1:
                        # Spread out multiple shots
                        angle_offset = (i - (self.multi_shot - 1) / 2) * 0.1
                        direction = self.facing.rotate(angle_offset * 30)
                    else:
                        direction = self.facing
                    
                    # Fire weapon pellets from player position
                    pellet_count = max(1, int(getattr(self.weapon, "pellets", 1)))
                    for _ in range(pellet_count):
                        bullet = self.weapon.fire(self.pos + direction * (PLAYER_RADIUS + 20), direction)
                        if bullet:
                            # Apply bullet speed multiplier
                            bullet.vel *= self.bullet_speed_multiplier
                            
                            # Apply damage multiplier
                            damage_mult = self.damage_multiplier
                            
                            # Critical strike chance
                            if random.random() < self.crit_chance:
                                damage_mult *= 2.0  # Double damage on crit
                                bullet.color = (255, 255, 100)  # Yellow for crit
                            
                            bullet.damage *= damage_mult
                            bullet.pierce = self.bullet_pierce
                            bullets.append(bullet)
                
                self.shoot_timer = 1 / fire_rate
                self.shoot_flash_timer = 0.08

        # Melee attack with right mouse button
        if mouse_pressed[2] and self.melee_cooldown <= 0:  # Right mouse button
            self.sword_swing_timer = 0.15
            # Create melee attack at player position
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

        # Draw level above character body
        self._draw_level_indicator(screen, screen_pos)
        
        # Level up effect particles
        if self.level_up_effect_timer > 0:
            self._draw_level_up_effect(screen, screen_pos)

    def _draw_level_indicator(self, screen, screen_pos):
        """Draw player level above character"""
        font = pygame.font.Font(None, 28)
        level_text = font.render(f"Lv.{self.player_level}", True, (255, 215, 0))
        text_rect = level_text.get_rect(center=(screen_pos.x, screen_pos.y - PLAYER_RADIUS - 20))
        
        # Draw background
        bg_rect = text_rect.inflate(10, 6)
        pygame.draw.rect(screen, (40, 40, 60, 200), bg_rect, border_radius=4)
        pygame.draw.rect(screen, (255, 215, 0, 150), bg_rect, 2, border_radius=4)
        
        screen.blit(level_text, text_rect)

    def _draw_level_up_effect(self, screen, screen_pos):
        """Draw particle effect for level up"""
        for i in range(8):
            angle = (pygame.time.get_ticks() / 100 + i * 45) * 0.0174533
            radius = 20 + (pygame.time.get_ticks() % 1000) / 1000 * 10
            x = screen_pos.x + math.cos(angle) * radius
            y = screen_pos.y + math.sin(angle) * radius
            
            color = (255, 215, 0)  # Gold color
            pygame.draw.circle(screen, color, (int(x), int(y)), 3)