# core/camera.py
import pygame

from core.settings import HEIGHT, WIDTH

class Camera:
    def __init__(self, screen_width, screen_height):
        self.camera = pygame.Rect(0, 0, screen_width, screen_height)
        self.width = screen_width
        self.height = screen_height
        
    def apply(self, entity):
        """Apply camera offset to an entity's position for drawing"""
        if hasattr(entity, 'pos'):
            # Since rooms are at (0, 0), no camera offset needed
            return pygame.Vector2(entity.pos.x, entity.pos.y)
        return pygame.Vector2(0, 0)
    
    def apply_pos(self, pos):
        """Apply camera offset to a position"""
        # Since rooms are at (0, 0), no camera offset needed
        return pygame.Vector2(pos.x, pos.y)
    
    def update(self, target):
        """No camera movement needed for single-screen gameplay"""
        pass