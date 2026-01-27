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
        """Update camera to follow target - but with single screen, just center on player"""
        if target:
            # Keep camera centered on player (though with single screen, camera is fixed)
            self.camera.x = target.pos.x - self.width // 2
            self.camera.y = target.pos.y - self.height // 2
            
            # Clamp to screen bounds (since we're in single screen mode)
            self.camera.x = max(0, min(self.camera.x, WIDTH - self.width))
            self.camera.y = max(0, min(self.camera.y, HEIGHT - self.height))