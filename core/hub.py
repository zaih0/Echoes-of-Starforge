# core/hub.py - UPDATED WITH FONT MANAGER
import pygame
import random
from typing import Dict, List
from core.settings import WIDTH, HEIGHT
from core.font_manager import font_manager  # ADD THIS
from core.save_manager import load_save_data, write_save_data

class SkillTree:
    def __init__(self):
        self.skills = {
            "health": {"level": 0, "max_level": 5, "cost": 3, "name": "Forge Heart", "description": "+20 Max HP per level"},
            "damage": {"level": 0, "max_level": 5, "cost": 2, "name": "Sharpened Edge", "description": "+10% Damage per level"},
            "speed": {"level": 0, "max_level": 5, "cost": 2, "name": "Swift Alloy", "description": "+5% Movement Speed per level"},
            "reload": {"level": 0, "max_level": 5, "cost": 3, "name": "Overclocked Core", "description": "+15% Fire Rate per level"},
            "luck": {"level": 0, "max_level": 5, "cost": 4, "name": "Lucky Strike", "description": "+10% Better Loot per level"},
            "crit": {"level": 0, "max_level": 5, "cost": 3, "name": "Precision Calibration", "description": "+5% Crit Chance per level"},
            "armor": {"level": 0, "max_level": 5, "cost": 3, "name": "Reinforced Plating", "description": "+10% Damage Reduction per level"},
            "regen": {"level": 0, "max_level": 5, "cost": 4, "name": "Self-Repair Nanites", "description": "+1 HP/s Regeneration per level"},
        }
        self.shards = 0
        self.total_shards_earned = 0
        
    def can_upgrade(self, skill_name):
        skill = self.skills.get(skill_name)
        if not skill:
            return False
        return skill["level"] < skill["max_level"] and self.shards >= skill["cost"]
    
    def upgrade(self, skill_name):
        if self.can_upgrade(skill_name):
            self.shards -= self.skills[skill_name]["cost"]
            self.skills[skill_name]["level"] += 1
            return True
        return False
    
    def get_bonuses(self):
        """Get all active bonuses from skill tree"""
        bonuses = {}
        for skill_name, skill in self.skills.items():
            if skill["level"] > 0:
                bonuses[skill_name] = skill["level"]
        return bonuses
    
    def save(self):
        data = {
            "shards": self.shards,
            "total_shards": self.total_shards_earned,
            "skills": {name: skill["level"] for name, skill in self.skills.items()}
        }
        write_save_data(data)
    
    def load(self):
        data = load_save_data()
        self.shards = data.get("shards", 0)
        self.total_shards_earned = data.get("total_shards", 0)
        skills_data = data.get("skills", {})
        for name, level in skills_data.items():
            if name in self.skills:
                self.skills[name]["level"] = min(level, self.skills[name]["max_level"])

class Hub:
    def __init__(self):
        self.skill_tree = SkillTree()
        self.skill_tree.load()
        self.selected_skill = 0
        self.skill_rects = []
        
        # Color scheme
        self.colors = {
            "bg": (15, 15, 25),
            "title": (100, 200, 255),
            "shard": (255, 215, 0),
            "skill_bg": (30, 35, 50),
            "skill_hover": (40, 50, 70),
            "skill_text": (230, 240, 255),
            "skill_desc": (180, 220, 255),
            "cost_available": (100, 255, 100),
            "cost_unavailable": (255, 100, 100),
            "progress_bg": (40, 45, 60),
            "progress_fill": (80, 180, 255),
            "instruction": (180, 200, 220)
        }
        
        # Hub visuals
        self.background = pygame.Surface((WIDTH, HEIGHT))
        self._create_background()

        # Hub lore snippets
        self.lore_lines = [
            "Forge Record: Each boss silenced reveals another echo of the fall.",
            "Spend Stellar Shards here to temper your next descent."
        ]
        
        # REMOVE OLD FONTS - USE FONT MANAGER INSTEAD
        
    def _create_background(self):
        """Create starry background for hub"""
        self.background.fill(self.colors["bg"])
        
        # Draw stars
        for _ in range(150):
            x = random.randint(0, WIDTH)
            y = random.randint(0, HEIGHT)
            size = random.uniform(0.5, 2.0)
            brightness = random.randint(150, 255)
            pygame.draw.circle(self.background, 
                             (brightness, brightness, brightness), 
                             (int(x), int(y)), size)
    
    def update(self, events):
        """Update hub state"""
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.selected_skill = max(0, self.selected_skill - 1)
                elif event.key == pygame.K_DOWN:
                    skill_names = list(self.skill_tree.skills.keys())
                    self.selected_skill = min(len(skill_names) - 1, self.selected_skill + 1)
                elif event.key == pygame.K_RETURN:
                    skill_names = list(self.skill_tree.skills.keys())
                    if self.selected_skill < len(skill_names):
                        self.skill_tree.upgrade(skill_names[self.selected_skill])
                elif event.key == pygame.K_ESCAPE:
                    return "menu"
        
        return "hub"
    
    def draw(self, screen):
        """Draw hub screen"""
        screen.blit(self.background, (0, 0))
        
        # Draw title with proper spacing
        title = font_manager.render("STARFORGE HUB", "title", self.colors["title"])
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 24))
        
        # Draw shard count with good spacing
        shard_text = font_manager.render(f"Stellar Shards: {self.skill_tree.shards}", 
                                       "large", self.colors["shard"])
        screen.blit(shard_text, (WIDTH//2 - shard_text.get_width()//2, 96))
        
        # Draw skill tree title
        tree_title = font_manager.render("STELLAR FORGE", "large", (180, 220, 255))
        screen.blit(tree_title, (WIDTH//2 - tree_title.get_width()//2, 160))
        
        # Draw total shards earned UNDER the Stellar Forge title
        total_text = font_manager.render(f"Total Shards Earned: {self.skill_tree.total_shards_earned}", 
                                       "normal", (200, 200, 200))
        screen.blit(total_text, (WIDTH//2 - total_text.get_width()//2, 206))

        # Lore panel
        lore_rect = pygame.Rect(WIDTH//2 - 620, 236, 1240, 44)
        pygame.draw.rect(screen, (20, 28, 48), lore_rect, border_radius=8)
        pygame.draw.rect(screen, (60, 100, 150), lore_rect, 2, border_radius=8)
        for i, line in enumerate(self.lore_lines):
            line_text = font_manager.render(line, "small", (190, 210, 235))
            screen.blit(line_text, (WIDTH//2 - line_text.get_width()//2, 242 + i * 18))
        
        # Draw skill tree
        self._draw_skill_tree(screen)
        
        # Draw instructions at the bottom
        instructions = [
            "UP/DOWN: Select Skill",
            "ENTER: Upgrade Selected Skill",
            "ESC: Return to Menu"
        ]
        
        for i, instruction in enumerate(instructions):
            text = font_manager.render(instruction, "small", self.colors["instruction"])
            screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT - 120 + i * 30))
    
    def _draw_skill_tree(self, screen):
        """Draw the skill tree interface"""
        skill_names = list(self.skill_tree.skills.keys())
        start_y = 292
        self.skill_rects = []
        
        # Draw skills with proper spacing
        for i, skill_name in enumerate(skill_names):
            skill = self.skill_tree.skills[skill_name]
            y = start_y + i * 72
            
            # Skill background color
            bg_color = self.colors["skill_hover"] if i == self.selected_skill else self.colors["skill_bg"]
            
            skill_rect = pygame.Rect(WIDTH//2 - 640, y, 1280, 64)
            self.skill_rects.append(skill_rect)
            pygame.draw.rect(screen, bg_color, skill_rect, border_radius=8)
            pygame.draw.rect(screen, (60, 100, 150), skill_rect, 2, border_radius=8)
            
            # Skill name
            name_text = font_manager.render(skill["name"], "normal", self.colors["skill_text"])
            screen.blit(name_text, (skill_rect.x + 18, skill_rect.y + 8))

            # Cost (top-right)
            cost_color = self.colors["cost_available"] if self.skill_tree.shards >= skill["cost"] else self.colors["cost_unavailable"]
            cost_text = font_manager.render(f"{skill['cost']} Shards", "normal", cost_color)
            screen.blit(cost_text, (skill_rect.right - cost_text.get_width() - 20, skill_rect.y + 8))
            
            # Level (bottom-left)
            level_text = font_manager.render(f"Level: {skill['level']}/{skill['max_level']}", 
                                           "small", (200, 200, 200))
            screen.blit(level_text, (skill_rect.x + 18, skill_rect.y + 37))
            
            # Description (bottom line, centered-right)
            desc_text = font_manager.render(skill["description"], "small", self.colors["skill_desc"])
            screen.blit(desc_text, (skill_rect.x + 340, skill_rect.y + 37))
            
            # Progress bar for skill level
            if skill["max_level"] > 0:
                progress_width = 240 * (skill["level"] / skill["max_level"])
                progress_rect = pygame.Rect(skill_rect.x + 340, skill_rect.y + 14, 240, 8)
                pygame.draw.rect(screen, self.colors["progress_bg"], progress_rect)
                pygame.draw.rect(screen, self.colors["progress_fill"], 
                               (progress_rect.x, progress_rect.y, progress_width, 8))