# core/menu.py
import pygame
import json
import os
import random
from core.settings import WIDTH, HEIGHT
from core.font_manager import font_manager  

class MainMenu:
    def __init__(self):
        self.selected_option = 0
        self.options = ["New Game", "Continue", "Hub", "Quit"]
        self.save_exists = os.path.exists("save_data.json")
        
        # Fonts using pixel font
        self.title_font = font_manager.get_font("title")
        self.option_font = font_manager.get_font("large")
        self.small_font = font_manager.get_font("normal")
        
        # Menu option rectangles for mouse clicks
        self.option_rects = []
        
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
        title_rect = title.get_rect(center=(WIDTH//2, HEIGHT//6))
        
        # Draw title glow
        for i in range(3):
            glow_surf = pygame.Surface((title_rect.width + i*4, title_rect.height + i*4), pygame.SRCALPHA)
            glow_color = (*self.colors["title"][:3], 30 - i*10)
            glow_text = self.title_font.render("ECHOES OF STARFORGE", True, glow_color)
            glow_surf.blit(glow_text, (i*2, i*2))
            screen.blit(glow_surf, (WIDTH//2 - glow_surf.get_width()//2, HEIGHT//6 - title_rect.height//2))
        
        screen.blit(title, title_rect)
        
        # Draw menu options with MORE SPACING
        self.option_rects = []
        start_y = HEIGHT//2 - 80  # Adjusted for better centering
        
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
            
            # Draw option with MORE VERTICAL SPACING
            option_surf = self.option_font.render(text, True, color)
            option_rect = option_surf.get_rect(center=(WIDTH//2, start_y + i * 100))  # Increased from 80 to 100
            
            # Store rectangle for mouse interaction (slightly larger)
            hover_rect = option_rect.inflate(80, 40)  # Increased from 60,30 to 80,40
            self.option_rects.append(hover_rect)
            
            # Draw hover effect
            if i == self.selected_option and enabled:
                # Draw a subtle glow behind the option
                glow_surf = pygame.Surface((hover_rect.width, hover_rect.height), pygame.SRCALPHA)
                pygame.draw.rect(glow_surf, self.colors["highlight"], 
                               glow_surf.get_rect(), border_radius=15)
                screen.blit(glow_surf, hover_rect)
                
                # Draw border
                pygame.draw.rect(screen, self.colors["border"], hover_rect, 3, border_radius=15)
            
            screen.blit(option_surf, option_rect)
            
            # Draw description for selected option (if enabled) with MORE SPACING
            if i == self.selected_option and enabled:
                desc = self._get_option_description(option)
                desc_surf = self.small_font.render(desc, True, self.colors["text"])
                desc_rect = desc_surf.get_rect(center=(WIDTH//2, start_y + i * 100 + 50))  # Increased from +40 to +50
                screen.blit(desc_surf, desc_rect)
        
        # Draw instructions at the bottom with MORE SPACING
        instructions = [
            "Use mouse or arrow keys to navigate",
            "Click or press ENTER to select",
            "Press ESC to quit"
        ]
        
        for i, instruction in enumerate(instructions):
            text = self.small_font.render(instruction, True, self.colors["instruction"])
            screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT - 150 + i * 35))  # Increased from 30 to 35
        
        # Draw version info
        version = "v0.1.0 | Echoes of Starforge"
        version_surf = self.small_font.render(version, True, (150, 150, 180))
        screen.blit(version_surf, (WIDTH//2 - version_surf.get_width()//2, HEIGHT - 40))
    
    def _get_option_description(self, option):
        """Get description for menu option"""
        descriptions = {
            "New Game": "Begin a new run. Your permanent upgrades are saved.",
            "Continue": "Resume your last run from where you left off.",
            "Hub": "Visit the Starforge to upgrade your permanent abilities.",
            "Quit": "Exit the game. Your progress is automatically saved."
        }
        return descriptions.get(option, "")