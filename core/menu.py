# core/menu.py
import pygame
import random
from core.settings import WIDTH, HEIGHT
from core.font_manager import font_manager  
from core.save_manager import has_run_save

class MainMenu:
    def __init__(self):
        self.selected_option = 0
        self.options = ["New Game", "Continue", "Hub", "Quit"]
        # Continue is only enabled when there is an in-progress run saved
        self.save_exists = has_run_save()
        
        # Fonts using pixel font
        self.title_font = font_manager.get_font("title")
        self.option_font = font_manager.get_font("large")
        self.small_font = font_manager.get_font("normal")
        
        # Menu option rectangles for mouse clicks
        self.option_rects = []

        # Story prologue (title screen)
        self.prologue_lines = [
            "The Starforge shattered and the vaults turned wild.",
            "You are a Forged Warden, sent to reclaim Stellar Shards.",
            "Descend. Survive. Rekindle the forge before the echoes consume it."
        ]
        
        # Color scheme that fits the aesthetic
        self.colors = {
            "bg": (10, 10, 20),
            "title": (100, 200, 255),  # Blue cyanish
            "option_normal": (200, 220, 255),  # Light blue
            "option_hover": (150, 220, 255),  # Brighter blue
            "option_disabled": (100, 100, 120),  # Gray
            "highlight": (80, 180, 255, 100),  # Transparent blue glow
            "border": (60, 150, 220),  # Blue border
            "text": (230, 240, 255),  # Off-white
            "instruction": (180, 200, 220)  # Light gray-blue
        }
    
    def update(self, events):
        """Update menu state"""
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()
        
        # Update selected option based on mouse hover
        self.selected_option = -1
        for i, rect in enumerate(self.option_rects):
            if rect.collidepoint(mouse_pos):
                self.selected_option = i
                break
        
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.selected_option = (self.selected_option - 1) % len(self.options)
                elif event.key == pygame.K_DOWN:
                    self.selected_option = (self.selected_option + 1) % len(self.options)
                elif event.key == pygame.K_RETURN:
                    return self._select_option()
                elif event.key == pygame.K_ESCAPE:
                    return "quit"
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and self.selected_option >= 0:
                    return self._select_option()
        
        return "menu"
    
    def _select_option(self):
        """Handle menu option selection"""
        if self.selected_option < 0:
            return "menu"
            
        option = self.options[self.selected_option]
        
        if option == "New Game":
            return "new_game"
        elif option == "Continue":
            if self.save_exists:
                return "continue"
            else:
                # Show a message or just stay in menu
                return "menu"
        elif option == "Hub":
            return "hub"
        elif option == "Quit":
            return "quit"
        
        return "menu"
    
    def draw(self, screen):
        """Draw the main menu"""
        screen.fill(self.colors["bg"])
        
        # Draw title with subtle glow effect
        title = self.title_font.render("ECHOES OF STARFORGE", True, self.colors["title"])
        title_rect = title.get_rect(center=(WIDTH//2, int(HEIGHT * 0.20)))
        
        # Draw title glow
        for i in range(3):
            glow_surf = pygame.Surface((title_rect.width + i*4, title_rect.height + i*4), pygame.SRCALPHA)
            glow_color = (*self.colors["title"][:3], 30 - i*10)
            glow_text = self.title_font.render("ECHOES OF STARFORGE", True, glow_color)
            glow_surf.blit(glow_text, (i*2, i*2))
            screen.blit(glow_surf, (WIDTH//2 - glow_surf.get_width()//2, title_rect.top - i*2))
        
        screen.blit(title, title_rect)
        
        # Subtitle / tagline
        tagline_surf = self.small_font.render("A dungeon-crawling adventure", True, (140, 170, 210))
        screen.blit(tagline_surf, tagline_surf.get_rect(center=(WIDTH//2, title_rect.bottom + 28)))

        # Prologue panel under title
        lore_top = title_rect.bottom + 52
        lore_line_h = 24
        lore_panel_h = 22 + lore_line_h * len(self.prologue_lines)
        lore_panel_w = min(1300, WIDTH - 240)
        lore_panel = pygame.Rect(WIDTH//2 - lore_panel_w//2, lore_top, lore_panel_w, lore_panel_h)
        pygame.draw.rect(screen, (15, 22, 45), lore_panel, border_radius=10)
        pygame.draw.rect(screen, self.colors["border"], lore_panel, 2, border_radius=10)

        for i, line in enumerate(self.prologue_lines):
            lore_text = font_manager.render(line, "small", self.colors["text"])
            lore_rect = lore_text.get_rect(centerx=WIDTH // 2, y=lore_top + 10 + i * lore_line_h)
            screen.blit(lore_text, lore_rect)
        
        # Draw menu options
        self.option_rects = []
        option_spacing = 145           # px between option centres
        total_h = (len(self.options) - 1) * option_spacing
        min_start_y = lore_panel.bottom + 34
        start_y = max(int(HEIGHT * 0.60) - total_h // 2, min_start_y)
        
        for i, option in enumerate(self.options):
            # Determine colors based on state
            if option == "Continue" and not self.save_exists:
                color = self.colors["option_disabled"]
                text = f"{option} (No Save)"
                enabled = False
            else:
                color = self.colors["option_hover"] if i == self.selected_option else self.colors["option_normal"]
                text = option
                enabled = True
            
            # Draw option with vertical spacing
            # Draw option
            option_surf = self.option_font.render(text, True, color)
            option_rect = option_surf.get_rect(center=(WIDTH//2, start_y + i * option_spacing))
            
            # Store rectangle for mouse interaction
            hover_rect = option_rect.inflate(140, 50)
            self.option_rects.append(hover_rect)
            
            # Draw hover effect
            if i == self.selected_option and enabled:
                glow_surf = pygame.Surface((hover_rect.width, hover_rect.height), pygame.SRCALPHA)
                pygame.draw.rect(glow_surf, self.colors["highlight"],
                               glow_surf.get_rect(), border_radius=15)
                screen.blit(glow_surf, hover_rect)
                pygame.draw.rect(screen, self.colors["border"], hover_rect, 3, border_radius=15)
            
            screen.blit(option_surf, option_rect)
        
        # Show description for selected option in a fixed panel below all buttons
        if 0 <= self.selected_option < len(self.options):
            sel_opt = self.options[self.selected_option]
            sel_enabled = not (sel_opt == "Continue" and not self.save_exists)
            if sel_enabled:
                desc = self._get_option_description(sel_opt)
                desc_y = start_y + total_h + 80
                desc_surf = self.small_font.render(desc, True, self.colors["text"])
                desc_rect = desc_surf.get_rect(centerx=WIDTH // 2, top=desc_y)
                box_rect = desc_rect.inflate(80, 24)
                pygame.draw.rect(screen, (15, 22, 45), box_rect, border_radius=10)
                pygame.draw.rect(screen, self.colors["border"], box_rect, 2, border_radius=10)
                screen.blit(desc_surf, desc_rect)
        
        # Draw instructions at the bottom
        instructions = [
            "Use mouse or arrow keys to navigate",
            "Click or press ENTER to select",
            "Press ESC to quit"
        ]
        
        instr_bottom = HEIGHT - 50
        instr_spacing = 34
        for i, instruction in enumerate(instructions):
            y = instr_bottom - (len(instructions) - 1 - i) * instr_spacing
            text = self.small_font.render(instruction, True, self.colors["instruction"])
            screen.blit(text, (WIDTH//2 - text.get_width()//2, y))
    
    def _get_option_description(self, option):
        """Get description for menu option"""
        descriptions = {
            "New Game": "Begin a new run. Your permanent upgrades are saved.",
            "Continue": "Resume your last run from where you left off.",
            "Hub": "Visit the Starforge to upgrade your permanent abilities.",
            "Quit": "Exit the game. Your progress is automatically saved."
        }
        return descriptions.get(option, "")