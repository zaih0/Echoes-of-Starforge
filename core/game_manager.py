# core/game_manager.py - COMPLETE FIXED VERSION
import pygame
import json
import os
from core.settings import WIDTH, HEIGHT, FPS, GRID_SIZE  # ADDED GRID_SIZE IMPORT
from core.menu import MainMenu
from core.hub import Hub
from core.dungeon_generator import DungeonGenerator
from core.levelup import LevelUpSystem
from core.camera import Camera
from entities.player import Player
from entities.weapon import starter_weapon, weapon_pool
from entities.charm import get_random_charm
from entities.bullet import Bullet
from entities.melee import SwordArc

class GameManager:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Game states
        self.state = "menu"  # menu, hub, game, dead
        self.menu = MainMenu()
        self.hub = Hub()
        
        # Game session
        self.player = None
        self.dungeon = None
        self.current_room = None
        self.rooms = []
        self.level_system = None
        self.bullets = []
        self.camera = Camera(WIDTH, HEIGHT)
        
        # Game stats
        self.current_level = 1
        self.room_number = 0
        self.kill_count = 0
        self.time_elapsed = 0
        self.game_paused = False
        
        # Font for UI - USE PIXEL FONT
        from core.font_manager import font_manager
        self.font_manager = font_manager
        
        # Debug - OFF by default
        self.debug = False
        
        # Load save data
        self.load_game()
    
    def load_game(self):
        """Load saved game data"""
        if os.path.exists("save_data.json"):
            with open("save_data.json", "r") as f:
                self.save_data = json.load(f)
        else:
            self.save_data = {}
    
    def save_game(self):
        """Save game data"""
        if self.hub:
            self.hub.skill_tree.save()
    
    def start_new_game(self):
        """Start a new game session"""
        print("=" * 50)
        print("STARTING NEW GAME")
        print("=" * 50)
    
        # Get skill bonuses from hub
        skill_bonuses = self.hub.skill_tree.get_bonuses() if self.hub else {}
        print(f"Skill bonuses: {skill_bonuses}")
    
        # Generate dungeon first
        print("Generating dungeon...")
        self.dungeon = DungeonGenerator(self.current_level)
        self.rooms = self.dungeon.generate(self.current_level)
        print(f"Generated {len(self.rooms)} rooms")
    
        # Start in start room
        self.current_room = self.dungeon.get_start_room()
    
        print(f"Current room: Index={self.current_room.index}, Type={self.current_room.room_type}")
        print(f"Room position: pixel_x={self.current_room.pixel_x}, pixel_y={self.current_room.pixel_y}")
        print(f"Room size: width={self.current_room.width}, height={self.current_room.height}")
    
        # Create player with skill bonuses at spawn position
        spawn_pos = self.current_room.get_player_spawn_position()
        print(f"Player spawn position: {spawn_pos}")
    
        self.player = Player(spawn_pos.x, spawn_pos.y, skill_bonuses)
        self.player.weapon = starter_weapon()
        print(f"Player created at: {self.player.pos}")
        print(f"Player weapon: {self.player.weapon.name}")
    
        # Initialize level system
        self.level_system = LevelUpSystem()
    
        # Reset game stats
        self.bullets = []
        self.kill_count = 0
        self.time_elapsed = 0
        self.room_number = self.current_room.index
    
        self.state = "game"
    
        # Debug: Check room contents
        print(f"Current room enemies: {len(self.current_room.enemies)}")
        print(f"Current room walls: {len(self.current_room.wall_rects)}")
        print(f"Current room doors: {len(self.current_room.door_rects)}")
        print("=" * 50)
    
    def continue_game(self):
        """Continue from save"""
        self.start_new_game()
    
    def return_to_hub(self):
        """Return to hub with earned shards"""
        if self.player and self.player.hp <= 0:
            # Player died, check if they earned shards
            shards_earned = self.kill_count // 10
            if shards_earned > 0:
                self.hub.skill_tree.shards += shards_earned
                self.hub.skill_tree.total_shards_earned += shards_earned
                self.save_game()
        
        self.state = "hub"
        self.player = None
        self.dungeon = None
        self.current_room = None
    
    def update(self, dt):
        """Update game based on current state"""
        events = pygame.event.get()
        
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
                return
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == "game":
                        if self.game_paused:
                            # If paused, unpause
                            self.game_paused = False
                        else:
                            # If not paused, pause the game
                            self.game_paused = True
                    elif self.state == "hub":
                        # From hub, go to main menu
                        self.state = "menu"
                    elif self.state == "dead":
                        # From death screen, go to main menu
                        self.state = "menu"
                    # Note: No ESC handling in "menu" state - menu handles its own ESC
                
                # Add M key to go to main menu from pause screen
                if event.key == pygame.K_m and self.state == "game" and self.game_paused:
                    self.state = "menu"
                    self.game_paused = False
                    self.player = None
                    self.dungeon = None
                    self.current_room = None
                
                if event.key == pygame.K_h and self.state == "game":
                    self.return_to_hub()
                    return
                
                # Debug key - F3 to toggle debug
                if event.key == pygame.K_F3:
                    self.debug = not self.debug
                    print(f"Debug mode: {self.debug}")
                
                # Level up selection
                if self.state == "game" and self.level_system and self.level_system.showing_upgrades:
                    if event.key in [pygame.K_1, pygame.K_2, pygame.K_3]:
                        upgrade_index = event.key - pygame.K_1
                        if upgrade_index < len(self.level_system.available_upgrades):
                            upgrade_name = self.level_system.apply_upgrade(self.player, upgrade_index)
                            if upgrade_name:
                                self.player.level_up_effect_timer = 2.0
                                self.player.player_level = self.level_system.player_level
        
        if self.state == "menu":
            result = self.menu.update(events)
            if result == "new_game":
                self.start_new_game()
            elif result == "continue":
                self.continue_game()
            elif result == "hub":
                self.state = "hub"
            elif result == "quit":
                self.running = False
        
        elif self.state == "hub":
            result = self.hub.update(events)
            if result == "menu":
                self.state = "menu"
        
        elif self.state == "game" and not self.game_paused:
            self._update_game(dt, events)
            
            # Check if player died
            if self.player and self.player.hp <= 0:
                self.state = "dead"
        
        elif self.state == "dead":
            self._update_death_screen(events)
    
    def _update_game(self, dt, events):
        """Update game gameplay"""
        self.time_elapsed += dt
        
        # Get mouse state
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()
        
        # Update camera first
        if self.player:
            self.camera.update(self.player)
        
        # Update player
        keys = pygame.key.get_pressed()
        if self.player:
            self.player.update(dt, self.bullets, keys, mouse_pos, mouse_pressed, self.current_room, self.camera)
        
        # Update bullets
        for bullet in self.bullets[:]:
            bullet.update(dt)
            if not bullet.alive:
                self.bullets.remove(bullet)
            
            # Check collision with walls
            bullet_rect = pygame.Rect(bullet.pos.x - bullet.radius, bullet.pos.y - bullet.radius, 
                                     bullet.radius * 2, bullet.radius * 2)
            for wall in self.current_room.wall_rects:
                if bullet_rect.colliderect(wall):
                    bullet.alive = False
                    break
            
            # Check collision with enemies
            for enemy in self.current_room.enemies[:]:
                if enemy.alive:
                    distance = (bullet.pos - enemy.pos).length()
                    if distance < bullet.radius + enemy.radius:
                        died = enemy.take_damage(bullet.damage, bullet.pos)
                        # Apply life steal
                        if died and self.player.life_steal > 0:
                            heal_amount = bullet.damage * self.player.life_steal
                            self.player.heal(heal_amount)
                        
                        # Check pierce
                        if bullet.pierce > 0:
                            bullet.pierce -= 1
                        else:
                            bullet.alive = False
                        
                        if died:
                            self.kill_count += 1
                        break
        
        # Update current room
        if self.current_room and self.player:
            keys = pygame.key.get_pressed()
            for result in self.current_room.update(self.player, dt, keys):
                if result[0] == "xp":
                    if self.level_system.add_xp(result[1]):
                        # Player leveled up
                        pass
                elif result[0] == "shard":
                    # Shards are collected immediately during run
                    pass
                elif result[0] == "exit":
                    # Player is exiting through a door
                    direction = result[1]
                    self._move_to_adjacent_room(direction)
        
        # Handle chest pickups separately
        if self.current_room and self.player:
            for chest in self.current_room.chests:
                if chest.pickup and chest.pickup.active and not chest.pickup.collected:
                    # Check if player is close to collect
                    distance = (self.player.pos - chest.pickup.pos).length()
                    if distance < 50 and chest.pickup.can_be_collected():
                        if chest.pickup.collect():
                            # Apply item to player
                            self._apply_item_to_player(chest.pickup.item)
                            print(f"Collected: {chest.pickup.item.name}")
        
        # Keep player in bounds
        if self.current_room and self.player:
            self.current_room.keep_player_in_bounds(self.player)
    
    def _move_to_adjacent_room(self, direction):
        """Move player to adjacent room"""
        if not self.dungeon or not self.current_room or not self.player:
            return
        
        # Calculate new grid position
        new_grid_x = self.current_room.grid_x + direction[1]
        new_grid_y = self.current_room.grid_y + direction[0]
        
        print(f"Attempting to move from room {self.current_room.index} at ({self.current_room.grid_x},{self.current_room.grid_y})")
        print(f"Direction: {direction}")
        print(f"New grid position: ({new_grid_x},{new_grid_y})")
        
        # Check if new position is within grid bounds
        if new_grid_x < 0 or new_grid_x >= GRID_SIZE or new_grid_y < 0 or new_grid_y >= GRID_SIZE:
            print(f"Cannot move: Position ({new_grid_x}, {new_grid_y}) is out of bounds")
            # Reset player position to center to prevent getting stuck at door
            self.player.pos = pygame.Vector2(WIDTH // 2, HEIGHT // 2)
            return
        
        # Get the adjacent room
        adjacent_room = self.dungeon.get_room_at(new_grid_x, new_grid_y)
        
        if adjacent_room:
            print(f"Moving to room {adjacent_room.index} at ({adjacent_room.grid_x},{adjacent_room.grid_y})")
            print(f"Room type: {adjacent_room.room_type}")
            print(f"Room connections: {adjacent_room.connections}")
            
            # Update current room
            self.current_room = adjacent_room
            self.room_number = self.current_room.index
            
            # Position player near the door they came from
            self._position_player_at_door((-direction[0], -direction[1]))
            
            # Clear bullets when changing rooms
            self.bullets.clear()
            
            # Mark room as visited
            self.current_room.visited = True
            
            print(f"Player positioned at: {self.player.pos}")
        else:
            print(f"No room at grid position ({new_grid_x}, {new_grid_y})")
            # Reset player position to center
            self.player.pos = pygame.Vector2(WIDTH // 2, HEIGHT // 2)
    
    def _position_player_at_door(self, from_direction):
        """Position player near the door they entered from"""
        if not self.player or not self.current_room:
            return
        
        # Get the door rect for the direction we came from
        door_rect = self.current_room.door_rects.get(from_direction)
        
        if door_rect:
            # Position player just inside the door, facing into the room
            offset = 30 + PLAYER_RADIUS  # Small offset from door
            
            if from_direction == (-1, 0):  # Came from top (entering bottom of room)
                self.player.pos = pygame.Vector2(
                    door_rect.centerx,
                    door_rect.bottom + offset
                )
            elif from_direction == (1, 0):  # Came from bottom (entering top of room)
                self.player.pos = pygame.Vector2(
                    door_rect.centerx,
                    door_rect.top - offset
                )
            elif from_direction == (0, -1):  # Came from left (entering right side of room)
                self.player.pos = pygame.Vector2(
                    door_rect.right + offset,
                    door_rect.centery
                )
            elif from_direction == (0, 1):  # Came from right (entering left side of room)
                self.player.pos = pygame.Vector2(
                    door_rect.left - offset,
                    door_rect.centery
                )
            print(f"Positioned player at door: {from_direction} -> {self.player.pos}")
        else:
            # Fallback to center if no door found
            print(f"WARNING: No door found for direction {from_direction}, positioning at center")
            self.player.pos = pygame.Vector2(WIDTH // 2, HEIGHT // 2)
    
    def _apply_item_to_player(self, item):
        """Apply collected item to player"""
        if not self.player:
            return
        
        # Check item type and apply accordingly
        if hasattr(item, 'type'):
            if item.type == "weapon":
                self.player.weapon = item
                print(f"Equipped new weapon: {item.name}")
            elif item.type == "charm":
                # Add charm to player
                self.player.add_charm(item)
    
    def _update_death_screen(self, events):
        """Update death screen"""
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.return_to_hub()
                elif event.key == pygame.K_ESCAPE:
                    self.state = "menu"
    
    def draw(self):
        """Draw game based on current state"""
        self.screen.fill((0, 0, 0))
        
        if self.state == "menu":
            self.menu.draw(self.screen)
        
        elif self.state == "hub":
            self.hub.draw(self.screen)
        
        elif self.state == "game":
            self._draw_game()
            
            if self.game_paused:
                self._draw_pause_menu()
            
            if self.level_system and self.level_system.showing_upgrades:
                self.level_system.draw(self.screen)
            
            # Draw UI elements
            self._draw_game_ui()
            
            # Draw start room tutorial text on the ground
            if self.current_room and self.current_room.room_type == "start":
                self._draw_start_room_tutorial()
            
            # Debug info (only if debug mode is on)
            if self.debug:
                self._draw_debug_info()
        
        elif self.state == "dead":
            self._draw_death_screen()
        
        pygame.display.flip()
    
    def _draw_game(self):
        """Draw gameplay"""
        # Draw current room
        if self.current_room:
            self.current_room.draw(self.screen, self.camera)
        
        # Draw chests
        for chest in self.current_room.chests:
            screen_pos = self.camera.apply_pos(chest.pos)
            chest.draw_at_position(self.screen, screen_pos)
        
        # Draw bullets
        for bullet in self.bullets:
            screen_pos = self.camera.apply_pos(bullet.pos)
            bullet.draw_at_position(self.screen, screen_pos)
        
        # Draw enemies
        for enemy in self.current_room.enemies:
            enemy.draw(self.screen, self.camera)
        
        # Draw melee attacks
        for melee in self.current_room.melees:
            melee.draw(self.screen, self.camera)
        
        # Draw XP pickups
        for xp in self.current_room.xp_pickups:
            xp.draw(self.screen, self.camera)
        
        # Draw shard pickups
        for shard in self.current_room.shard_pickups:
            shard.draw(self.screen, self.camera)
    
        # Draw player
        if self.player:
            self.player.draw(self.screen, self.camera)
    
    def _draw_game_ui(self):
        """Draw clean game UI elements"""
        # Top-left: Health bar
        self._draw_health_bar()
        
        # Top-left under health: XP bar
        if self.level_system:
            self._draw_xp_bar()
        
        # Top-right: Weapon and Charms
        self._draw_equipment_panel()
        
        # Room info at bottom-left
        if self.current_room:
            self._draw_room_info()
        
        # REMOVED: Controls hint at bottom (now in start room tutorial only)
        # Only show controls hint if NOT in start room
        if self.current_room and self.current_room.room_type != "start":
            controls = "WASD: Move | Mouse: Aim/Shoot | E: Open Chests | ESC: Pause | H: Hub | F3: Debug"
            controls_text = self.font_manager.render(controls, "normal", (180, 180, 180))
            self.screen.blit(controls_text, (WIDTH//2 - controls_text.get_width()//2, HEIGHT - 40))
        
        # Door navigation hint (only if not in start room)
        if (self.current_room and self.current_room.room_type != "start" and 
            self.current_room.cleared and len(self.current_room.door_rects) > 0):
            nav_text = self.font_manager.render("Walk through open doors to explore", "normal", (200, 200, 100))
            self.screen.blit(nav_text, (WIDTH//2 - nav_text.get_width()//2, HEIGHT - 80))
    
    def _draw_health_bar(self):
        """Draw health bar in top-left corner"""
        if not self.player:
            return
        
        # Health bar background
        bar_width = 400
        bar_height = 40
        bar_x = 30
        bar_y = 30
        
        # Background
        pygame.draw.rect(self.screen, (40, 40, 60), (bar_x, bar_y, bar_width, bar_height), border_radius=5)
        pygame.draw.rect(self.screen, (60, 60, 80), (bar_x, bar_y, bar_width, bar_height), 3, border_radius=5)
        
        # Health fill
        health_ratio = self.player.hp / self.player.max_hp
        fill_width = max(0, int(bar_width * health_ratio))
        
        # Color based on health percentage
        if health_ratio > 0.6:
            color = (80, 220, 80)  # Green
        elif health_ratio > 0.3:
            color = (220, 220, 80)  # Yellow
        else:
            color = (220, 80, 80)  # Red
        
        pygame.draw.rect(self.screen, color, (bar_x + 2, bar_y + 2, fill_width - 4, bar_height - 4), border_radius=3)
        
        # Health text - USING PIXEL FONT - CHANGED TO "small"
        health_text = f"HEALTH: {int(self.player.hp)}/{int(self.player.max_hp)}"
        text_surface = self.font_manager.render(health_text, "small", (255, 255, 255))
        text_x = bar_x + (bar_width - text_surface.get_width()) // 2
        text_y = bar_y + (bar_height - text_surface.get_height()) // 2
        self.screen.blit(text_surface, (text_x, text_y))
    
    def _draw_xp_bar(self):
        """Draw XP bar under health bar"""
        bar_width = 400
        bar_height = 25
        bar_x = 30
        bar_y = 85  # Under health bar
        
        # Background
        pygame.draw.rect(self.screen, (30, 40, 50), (bar_x, bar_y, bar_width, bar_height), border_radius=3)
        pygame.draw.rect(self.screen, (50, 60, 70), (bar_x, bar_y, bar_width, bar_height), 2, border_radius=3)
        
        # XP fill
        xp_ratio = self.level_system.xp / self.level_system.xp_to_next_level
        fill_width = max(0, int(bar_width * xp_ratio))
        
        # Blue-green gradient color
        fill_color = (100, 220, 255)  # Blue-green
        
        pygame.draw.rect(self.screen, fill_color, (bar_x + 2, bar_y + 2, fill_width - 4, bar_height - 4), border_radius=2)
        
        # XP text
        xp_text = f"XP: {self.level_system.xp}/{self.level_system.xp_to_next_level} (Level {self.level_system.player_level})"
        text_surface = self.font_manager.render(xp_text, "small", (220, 240, 255))
        text_x = bar_x + (bar_width - text_surface.get_width()) // 2
        text_y = bar_y + (bar_height - text_surface.get_height()) // 2
        self.screen.blit(text_surface, (text_x, text_y))
    
    def _draw_equipment_panel(self):
        """Draw weapon and charms in top-right corner"""
        panel_x = WIDTH - 450
        panel_y = 30
        panel_width = 420
        item_height = 40
        
        # Panel background
        pygame.draw.rect(self.screen, (40, 40, 60, 220), (panel_x, panel_y, panel_width, 200), border_radius=5)
        pygame.draw.rect(self.screen, (60, 80, 100), (panel_x, panel_y, panel_width, 200), 2, border_radius=5)
        
        # Panel title
        title_text = self.font_manager.render("EQUIPMENT", "normal", (180, 220, 255))
        self.screen.blit(title_text, (panel_x + 20, panel_y + 10))
        
        # Weapon slot
        weapon_y = panel_y + 50
        if self.player and self.player.weapon:
            weapon_text = self.font_manager.render(f"WEAPON: {self.player.weapon.name}", "small", (140, 220, 255))
            self.screen.blit(weapon_text, (panel_x + 20, weapon_y))
        
        # Charms slots
        charms_y = panel_y + 90
        charms_title = self.font_manager.render("CHARMS:", "small", (190, 140, 255))
        self.screen.blit(charms_title, (panel_x + 20, charms_y))
        
        if self.player and self.player.charms:
            for i, charm in enumerate(self.player.charms[:5]):  # Show up to 5 charms
                charm_y = charms_y + 30 + (i * 25)
                charm_text = self.font_manager.render(f"• {charm.name}: {charm.description}", "small", (220, 200, 255))
                self.screen.blit(charm_text, (panel_x + 40, charm_y))
        
        # Show charm count if more than 5
        if self.player and len(self.player.charms) > 5:
            count_text = self.font_manager.render(f"+{len(self.player.charms) - 5} more...", "small", (180, 180, 220))
            self.screen.blit(count_text, (panel_x + 40, charms_y + 30 + (5 * 25)))
    
    def _draw_room_info(self):
        """Draw room information at bottom-left"""
        info_x = 30
        info_y = HEIGHT - 150
        
        # Background
        pygame.draw.rect(self.screen, (40, 40, 60, 180), (info_x, info_y, 300, 120), border_radius=5)
        pygame.draw.rect(self.screen, (60, 80, 100), (info_x, info_y, 300, 120), 2, border_radius=5)
        
        # Room info
        room_type = self.current_room.room_type.upper()
        room_text = self.font_manager.render(f"ROOM: {room_type}", "normal", (200, 255, 200))
        self.screen.blit(room_text, (info_x + 20, info_y + 15))
        
        enemies_text = self.font_manager.render(f"Enemies: {len(self.current_room.enemies)}", "small", (255, 150, 150))
        self.screen.blit(enemies_text, (info_x + 20, info_y + 55))
        
        cleared_text = self.font_manager.render(f"Cleared: {'YES' if self.current_room.cleared else 'NO'}", 
                                              "small", (150, 255, 150) if self.current_room.cleared else (255, 150, 150))
        self.screen.blit(cleared_text, (info_x + 20, info_y + 85))
    
    def _draw_start_room_tutorial(self):
        """Draw tutorial text on the ground in start room"""
        # Create a semi-transparent surface for the tutorial area
        tutorial_surface = pygame.Surface((WIDTH - 200, HEIGHT - 300), pygame.SRCALPHA)
        tutorial_surface.fill((20, 25, 35, 180))
        
        # Position it in the center of the screen
        tutorial_rect = tutorial_surface.get_rect(center=(WIDTH//2, HEIGHT//2))
        self.screen.blit(tutorial_surface, tutorial_rect)
        
        # Draw border
        pygame.draw.rect(self.screen, (60, 80, 100, 200), tutorial_rect, 3, border_radius=10)
        
        # Tutorial title
        title = self.font_manager.render("ECHOES OF STARFORGE", "large", (100, 200, 255))
        title_rect = title.get_rect(center=(WIDTH//2, HEIGHT//2 - 120))
        self.screen.blit(title, title_rect)
        
        # Tutorial subtitle
        subtitle = self.font_manager.render("Begin your journey through the forge", "medium", (180, 220, 255))
        subtitle_rect = subtitle.get_rect(center=(WIDTH//2, HEIGHT//2 - 70))
        self.screen.blit(subtitle, subtitle_rect)
        
        # Controls instructions
        controls = [
            "CONTROLS:",
            "WASD - Move your character",
            "Mouse - Aim and shoot",
            "Left Click - Fire weapon",
            "Right Click - Melee attack",
            "E - Open chests and interact",
            "ESC - Pause game",
            "F3 - Toggle debug information",
            "H - Return to hub (keep shards)"
        ]
        
        for i, control in enumerate(controls):
            color = (255, 215, 0) if i == 0 else (220, 240, 255)
            font_size = "medium" if i == 0 else "small"
            text = self.font_manager.render(control, font_size, color)
            text_rect = text.get_rect(center=(WIDTH//2, HEIGHT//2 - 20 + (i * 35)))
            self.screen.blit(text, text_rect)
        
        # Start hint
        start_hint = self.font_manager.render("Walk through any open door to begin your adventure", 
                                           "normal", (200, 255, 200))
        start_hint_rect = start_hint.get_rect(center=(WIDTH//2, HEIGHT//2 + 200))
        self.screen.blit(start_hint, start_hint_rect)
    
    def _draw_debug_info(self):
        """Draw debug information"""
        debug_info = [
            f"State: {self.state}",
            f"Player: ({self.player.pos.x:.1f}, {self.player.pos.y:.1f})" if self.player else "Player: None",
            f"Player HP: {self.player.hp}/{self.player.max_hp}" if self.player else "Player HP: N/A",
            f"Player Level: {self.player.player_level}" if self.player else "Player Level: N/A",
            f"Camera: {self.camera.camera}",
            f"Current Room: {self.current_room.index} ({self.current_room.grid_x},{self.current_room.grid_y})" if self.current_room else "Current Room: None",
            f"Room Type: {self.current_room.room_type}" if self.current_room else "Room Type: None",
            f"Enemies: {len(self.current_room.enemies)}" if self.current_room else "Enemies: N/A",
            f"Doors: {len(self.current_room.door_rects)}" if self.current_room else "Doors: N/A",
            f"Cleared: {self.current_room.cleared}" if self.current_room else "Cleared: N/A",
            f"Connections: {len(self.current_room.connections)}" if self.current_room else "Connections: N/A",
            f"Bullets: {len(self.bullets)}",
            f"Chests: {len(self.current_room.chests)}" if self.current_room else "Chests: N/A",
            f"Kills: {self.kill_count}",
            f"Time: {self.time_elapsed:.1f}s",
            f"FPS: {int(self.clock.get_fps())}"
        ]
        
        for i, info in enumerate(debug_info):
            debug_text = self.font_manager.render(info, "small", (255, 100, 100))
            self.screen.blit(debug_text, (10, 10 + i * 25))
    
    def _draw_pause_menu(self):
        """Draw pause menu overlay"""
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        pause_text = self.font_manager.render("PAUSED", "large", (255, 255, 255))
        self.screen.blit(pause_text, (WIDTH//2 - pause_text.get_width()//2, HEIGHT//2 - 100))
        
        resume_text = self.font_manager.render("Press ESC to resume", "normal", (200, 200, 200))
        self.screen.blit(resume_text, (WIDTH//2 - resume_text.get_width()//2, HEIGHT//2 + 50))
        
        # Add menu option in pause screen
        menu_text = self.font_manager.render("Press M to return to Main Menu", "normal", (200, 200, 100))
        self.screen.blit(menu_text, (WIDTH//2 - menu_text.get_width()//2, HEIGHT//2 + 100))
    
    def _draw_death_screen(self):
        """Draw death screen"""
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        self.screen.blit(overlay, (0, 0))
        
        death_text = self.font_manager.render("THE FORGE FADES...", "large", (255, 50, 50))
        self.screen.blit(death_text, (WIDTH//2 - death_text.get_width()//2, HEIGHT//2 - 100))
        
        stats_text = self.font_manager.render(f"Rooms Cleared: {self.room_number} | Kills: {self.kill_count}", 
                                            "medium", (255, 200, 100))
        self.screen.blit(stats_text, (WIDTH//2 - stats_text.get_width()//2, HEIGHT//2 - 30))
        
        options = [
            "Press ENTER to return to Hub",
            "Press ESC for Main Menu"
        ]
        
        for i, option in enumerate(options):
            option_text = self.font_manager.render(option, "normal", (200, 200, 100))
            self.screen.blit(option_text, (WIDTH//2 - option_text.get_width()//2, 
                                         HEIGHT//2 + 50 + i * 50))
    
    def run(self):
        """Main game loop"""
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            
            self.update(dt)
            self.draw()
            
            # Auto-save every minute
            if pygame.time.get_ticks() % 60000 < 16:
                self.save_game()
        
        self.save_game()
        pygame.quit()
    
    def cleanup(self):
        """Clean up resources"""
        if self.player:
            del self.player
        if self.dungeon:
            del self.dungeon
        self.bullets.clear()