import pygame, math, random
from core.settings import *
from entities.bullet import Bullet
from entities.melee import MeleeAttack

class Player:
    def __init__(self, x, y):
        self.pos = pygame.Vector2(x, y)
        self.weapon = None
        self.cooldown = 0
        self.hp = PLAYER_MAX_HP
        self.muzzle_flash = 0
        self.melee_attacks = []

    def update(self, dt, bullets, keys, enemies):
        move = pygame.Vector2(keys[pygame.K_d]-keys[pygame.K_a],
                              keys[pygame.K_s]-keys[pygame.K_w])
        if move.length_squared():
            self.pos += move.normalize() * PLAYER_SPEED * dt

        self.cooldown = max(0, self.cooldown - dt)
        self.muzzle_flash = max(0, self.muzzle_flash - dt)

        if self.weapon and self.cooldown <= 0:
            aim = pygame.Vector2(pygame.mouse.get_pos()) - self.pos
            if aim.length_squared():
                if self.weapon.type == "ranged" and pygame.mouse.get_pressed()[0]:
                    bullets.append(Bullet(self.pos + aim.normalize()*18,
                                          aim.normalize()*self.weapon.speed,
                                          self.weapon.damage))
                    self.cooldown = 1/self.weapon.fire_rate
                    self.muzzle_flash = 0.08
                elif self.weapon.type == "melee" and pygame.mouse.get_pressed()[0]:
                    self.melee_attacks.append(MeleeAttack(self.pos, aim, self.weapon))
                    self.cooldown = 1/self.weapon.fire_rate

        for m in self.melee_attacks:
            m.update(dt, enemies)
        self.melee_attacks = [m for m in self.melee_attacks if m.alive]

    def draw(self, screen):
        pygame.draw.circle(screen, (220,220,255), self.pos, PLAYER_RADIUS)
        if self.muzzle_flash > 0:
            # muzzle flash with particles
            pygame.draw.circle(screen, (255,255,200), self.pos, 18, 2)
            for _ in range(3):
                offset = pygame.Vector2(random.uniform(-10,10), random.uniform(-10,10))
                pygame.draw.circle(screen, (255,230,120), self.pos+offset, 4)
        for m in self.melee_attacks:
            m.draw(screen)
        # health bar
        w = 40
        pct = max(0, self.hp/PLAYER_MAX_HP)
        pygame.draw.rect(screen, (60,60,60), (20, HEIGHT-20, w, 6))
        pygame.draw.rect(screen, (240,80,80), (20, HEIGHT-20, w*pct, 6))
