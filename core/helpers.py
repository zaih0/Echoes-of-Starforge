import pygame
import random
import math
from core.settings import WIDTH, HEIGHT

def clamp(vx, vy):
    l = math.hypot(vx, vy)
    return (vx/l, vy/l) if l else (0,0)

def angle_to_unit(angle):
    return pygame.Vector2(math.cos(angle), math.sin(angle))

def vec_to_angle(v):
    return math.atan2(v.y, v.x)

def circle_hit(a, ar, b, br):
    return (a - b).length_squared() <= (ar + br) ** 2

def spawn_position_outside_screen(m=40):
    side = random.choice("tblr")
    if side == "t": return pygame.Vector2(random.uniform(0, WIDTH), -m)
    if side == "b": return pygame.Vector2(random.uniform(0, WIDTH), HEIGHT + m)
    if side == "l": return pygame.Vector2(-m, random.uniform(0, HEIGHT))
    return pygame.Vector2(WIDTH + m, random.uniform(0, HEIGHT))

def random_point_in_arena(m=60):
    return pygame.Vector2(random.uniform(m, WIDTH-m), random.uniform(m, HEIGHT-m))
