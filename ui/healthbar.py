import pygame

def draw_health_bar(surface, pos, current, maximum):
    width = 26
    height = 4
    pct = max(0, current / maximum)
    x = pos.x - width // 2
    y = pos.y - 22
    pygame.draw.rect(surface, (60,60,60), (x, y, width, height))
    pygame.draw.rect(surface, (200,60,60), (x, y, width * pct, height))
