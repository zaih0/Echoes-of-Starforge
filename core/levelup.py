# core/levelup.py
import pygame
import random
from core.settings import WIDTH, HEIGHT

class LevelUpSystem:
    def __init__(self):
        self.player_level = 1
        self.xp = 0
        self.xp_to_next_level = 100
        self.available_upgrades = []
        self.showing_upgrades = False
        
        # Upgrade options pool (no emojis)
        self.upgrade_pool = [
            {
                "name": "Health Boost",
                "description": "+25 Max HP",
                "apply": lambda p: setattr(p, 'max_hp', p.max_hp + 25)
            },
            {
                "name": "Damage Boost",
                "description": "+15% Damage",
                "apply": lambda p: setattr(p, 'damage_multiplier', getattr(p, 'damage_multiplier', 1.0) * 1.15)
            },
            {
                "name": "Speed Boost",
                "description": "+20% Movement Speed",
                "apply": lambda p: setattr(p, 'speed', p.speed * 1.2)
            },
            {
                "name": "Fire Rate",
                "description": "+25% Fire Rate",
                "apply": lambda p: setattr(p, 'fire_rate_multiplier', getattr(p, 'fire_rate_multiplier', 1.0) * 1.25)
            },
            {
                "name": "Life Steal",
                "description": "Heal 10% of damage dealt",
                "apply": lambda p: setattr(p, 'life_steal', 0.1)
            },
            {
                "name": "Critical Chance",
                "description": "+15% Critical Strike Chance",
                "apply": lambda p: setattr(p, 'crit_chance', getattr(p, 'crit_chance', 0.0) + 0.15)
            },
            {
                "name": "Bullet Speed",
                "description": "+30% Bullet Speed",
                "apply": lambda p: setattr(p, 'bullet_speed_multiplier', getattr(p, 'bullet_speed_multiplier', 1.0) * 1.3)
            },
            {
                "name": "Health Regeneration",
                "description": "Regenerate 2 HP per second",
                "apply": lambda p: setattr(p, 'health_regen', getattr(p, 'health_regen', 0.0) + 2.0)
            },
            {
                "name": "Damage Reduction",
                "description": "Take 20% less damage",
                "apply": lambda p: setattr(p, 'damage_reduction', getattr(p, 'damage_reduction', 0.0) + 0.2)
            },
            {
                "name": "Double Shot",
                "description": "Fire 2 bullets at once",
                "apply": lambda p: setattr(p, 'multi_shot', 2)
            },
        ]
    
    def add_xp(self, amount):
        self.xp += amount
        if self.xp >= self.xp_to_next_level:
            self.level_up()
            return True
        return False
    
    def level_up(self):
        self.player_level += 1
        self.xp -= self.xp_to_next_level
        self.xp_to_next_level = int(self.xp_to_next_level * 1.5)
        
        # Pick 3 random upgrades
        self.available_upgrades = random.sample(self.upgrade_pool, 3)
        self.showing_upgrades = True
    
    def apply_upgrade(self, player, upgrade_index):
        if 0 <= upgrade_index < len(self.available_upgrades):
            upgrade = self.available_upgrades[upgrade_index]
            upgrade["apply"](player)
            self.showing_upgrades = False
            return upgrade["name"]
        return None
    
    def draw(self, screen):
        if not self.showing_upgrades:
            return
        
        # Semi-transparent overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))
        
        # Title
        font_large = pygame.font.Font(None, 72)
        title = font_large.render("LEVEL UP!", True, (255, 215, 0))
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 50))
        
        font_medium = pygame.font.Font(None, 48)
        level_text = font_medium.render(f"Level {self.player_level}", True, (255, 255, 255))
        screen.blit(level_text, (WIDTH//2 - level_text.get_width()//2, 130))
        
        font_small = pygame.font.Font(None, 32)
        instruction = font_small.render("Choose an upgrade (1-3):", True, (200, 200, 200))
        screen.blit(instruction, (WIDTH//2 - instruction.get_width()//2, 180))
        
        # Draw upgrade options
        for i, upgrade in enumerate(self.available_upgrades):
            y = 250 + i * 120
            
            # Upgrade box
            box_rect = pygame.Rect(WIDTH//2 - 250, y, 500, 100)
            pygame.draw.rect(screen, (40, 50, 70), box_rect, border_radius=10)
            pygame.draw.rect(screen, (80, 100, 120), box_rect, 3, border_radius=10)
            
            # Number indicator
            num_font = pygame.font.Font(None, 36)
            num_text = num_font.render(str(i+1), True, (255, 215, 0))
            screen.blit(num_text, (box_rect.x + 20, box_rect.centery - num_text.get_height()//2))
            
            # Upgrade name
            name_font = pygame.font.Font(None, 36)
            name_text = name_font.render(upgrade["name"], True, (255, 255, 255))
            screen.blit(name_text, (box_rect.x + 60, box_rect.y + 20))
            
            # Description
            desc_font = pygame.font.Font(None, 24)
            desc_text = desc_font.render(upgrade["description"], True, (180, 220, 255))
            screen.blit(desc_text, (box_rect.x + 60, box_rect.y + 55))