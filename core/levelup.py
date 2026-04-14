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
        overlay.fill((0, 0, 0, 210))
        screen.blit(overlay, (0, 0))

        # --- Fonts ---
        font_title  = pygame.font.Font(None, 96)
        font_level  = pygame.font.Font(None, 56)
        font_hint   = pygame.font.Font(None, 40)
        font_name   = pygame.font.Font(None, 52)
        font_desc   = pygame.font.Font(None, 36)
        font_num    = pygame.font.Font(None, 56)

        # --- Card dimensions (scale to screen) ---
        card_w   = min(900, WIDTH - 200)
        card_h   = 150
        card_gap = 28
        cards_total_h = len(self.available_upgrades) * (card_h + card_gap) - card_gap

        # --- Vertical layout ---
        header_h   = 240          # space reserved above the cards
        block_h    = header_h + cards_total_h + 60   # +60 for hint below
        block_top  = HEIGHT // 2 - block_h // 2

        title_y    = block_top + 10
        level_y    = title_y + 90
        cards_top  = block_top + header_h
        hint_y     = cards_top + cards_total_h + 20

        # --- Title ---
        title_surf = font_title.render("LEVEL UP!", True, (255, 215, 0))
        screen.blit(title_surf, title_surf.get_rect(centerx=WIDTH // 2, top=title_y))

        # Level sub-text
        level_surf = font_level.render(f"Now Level {self.player_level}", True, (220, 240, 255))
        screen.blit(level_surf, level_surf.get_rect(centerx=WIDTH // 2, top=level_y))

        # --- Upgrade cards ---
        card_x = WIDTH // 2 - card_w // 2
        for i, upgrade in enumerate(self.available_upgrades):
            card_y = cards_top + i * (card_h + card_gap)
            box_rect = pygame.Rect(card_x, card_y, card_w, card_h)

            # Card background
            pygame.draw.rect(screen, (30, 40, 65), box_rect, border_radius=14)
            pygame.draw.rect(screen, (90, 120, 180), box_rect, 3, border_radius=14)

            # Number badge
            badge_rect = pygame.Rect(box_rect.x + 20, box_rect.centery - 28, 56, 56)
            pygame.draw.rect(screen, (255, 215, 0), badge_rect, border_radius=10)
            num_surf = font_num.render(str(i + 1), True, (20, 20, 40))
            screen.blit(num_surf, num_surf.get_rect(center=badge_rect.center))

            # Upgrade name
            name_surf = font_name.render(upgrade["name"], True, (255, 255, 255))
            screen.blit(name_surf, (box_rect.x + 96, box_rect.y + 28))

            # Description
            desc_surf = font_desc.render(upgrade["description"], True, (160, 210, 255))
            screen.blit(desc_surf, (box_rect.x + 96, box_rect.y + 86))

        # --- Hint ---
        hint_surf = font_hint.render("Press  1 / 2 / 3  to choose", True, (180, 180, 200))
        screen.blit(hint_surf, hint_surf.get_rect(centerx=WIDTH // 2, top=hint_y))