# entities/melee.py
import pygame
import math

class SwordArc:
    def __init__(self, pos, direction):
        self.pos = pygame.Vector2(pos)
        self.dir = direction.normalize() if direction.length_squared() > 0 else pygame.Vector2(1, 0)
        self.timer = 0.15
        self.active = True
        self.damage = 35
        self.radius = 50
        self.arc_angle = math.radians(90)  # 90 degree arc

    def update(self, dt):
        self.timer -= dt
        if self.timer <= 0:
            self.active = False

    def hits(self, enemy):
        if not enemy.alive:
            return False

        to_enemy = enemy.pos - self.pos
        distance = to_enemy.length()
        
        if distance > self.radius:
            return False

        if distance == 0:
            return True

        # Calculate angle between swing direction and enemy direction
        angle = math.atan2(self.dir.y, self.dir.x) - math.atan2(to_enemy.y, to_enemy.x)
        # Normalize angle to [-pi, pi]
        angle = (angle + math.pi) % (2 * math.pi) - math.pi
        
        return abs(angle) < self.arc_angle / 2

    def draw(self, screen, camera_offset=(0, 0)):
        offset_x, offset_y = camera_offset
        draw_pos = pygame.Vector2(self.pos.x - offset_x, self.pos.y - offset_y)
        
        # Calculate arc angles
        start_angle = math.atan2(self.dir.y, self.dir.x) - self.arc_angle / 2
        end_angle = start_angle + self.arc_angle
        
        # Draw arc
        rect = pygame.Rect(
            draw_pos.x - self.radius,
            draw_pos.y - self.radius,
            self.radius * 2,
            self.radius * 2
        )
        
        # Fade out as timer decreases
        alpha = int(255 * (self.timer / 0.15))
        color = (240, 240, 200, alpha)
        
        # Create a surface for the arc with transparency
        arc_surface = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.arc(arc_surface, color, arc_surface.get_rect(), start_angle, end_angle, 4)
        screen.blit(arc_surface, (draw_pos.x - self.radius, draw_pos.y - self.radius))