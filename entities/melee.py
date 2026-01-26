import pygame, math
from core.settings import *

def vec_to_angle(v):
    return math.atan2(v.y, v.x)

def angle_to_unit_vec(angle):
    return pygame.Vector2(math.cos(angle), math.sin(angle))

class MeleeAttack:
    """
    Represents a swinging melee arc for a few frames.
    """
    def __init__(self, player_pos, aim_dir, weapon):
        self.pos = pygame.Vector2(player_pos)
        self.angle = math.atan2(aim_dir.y, aim_dir.x)
        self.weapon = weapon
        self.duration = 0.18    # seconds
        self.age = 0.0
        self.arc_radius = 50
        self.arc_angle = math.pi / 3  # 60 degrees
        self.hit_enemies = set()
        self.alive = True

    def update(self, dt, enemies: list):
        self.age += dt
        if self.age >= self.duration:
            self.alive = False
            return

        # Damage enemies in arc
        for e in enemies:
            if not e.alive or e in self.hit_enemies:
                continue
            dir_to_enemy = e.pos - self.pos
            dist = dir_to_enemy.length()
            if dist > self.arc_radius:
                continue
            angle_to_enemy = math.atan2(dir_to_enemy.y, dir_to_enemy.x)
            diff = (angle_to_enemy - self.angle + math.pi) % (2*math.pi) - math.pi
            if abs(diff) <= self.arc_angle / 2:
                e.take_damage(self.weapon.damage)
                self.hit_enemies.add(e)
                if getattr(self.weapon, "effect", None) == "burn":
                    e.burn_timer = getattr(e, "burn_timer", 0.0) + 2.0

    def draw(self, screen):
        alpha = max(0, int(200 * (1 - self.age / self.duration)))
        surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        start_angle = self.angle - self.arc_angle / 2
        end_angle = self.angle + self.arc_angle / 2
        points = [self.pos]
        for a in [start_angle, end_angle]:
            points.append(self.pos + pygame.Vector2(math.cos(a), math.sin(a)) * self.arc_radius)
        pygame.draw.polygon(surf, (255, 180, 60, alpha), points)
        screen.blit(surf, (0,0))
