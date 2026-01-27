# core/game_manager.py
import pygame
import json
import os
from core.settings import WIDTH, HEIGHT
from core.menu import MainMenu
from core.hub import Hub
from core.dungeon_generator import DungeonGenerator
from core.levelup import LevelUpSystem
from core.camera import Camera
from entities.player import Player
from entities.weapon import starter_weapon

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
        
        # Font for UI
        self.font = pygame.font.Font(None, 32)
        self.large_font = pygame.font.Font(None, 64)
        
        # Debug
        self.debug = True
        
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
    
    # FOR TESTING: Start in the first non-start room (room with enemies)
    # Find first room that's not start and has enemies
        test_room = None
        for room in self.rooms:
            if room.room_type != "start" and len(room.enemies) > 0:
             test_room = room
            break
    
        if test_room:
            self.current_room = test_room
            print(f"TESTING: Starting in room {test_room.index} ({test_room.room_type}) with {len(test_room.enemies)} enemies")
        else:
        # Fallback to start room
            self.current_room = self.dungeon.get_start_room()
            print("WARNING: No non-start rooms with enemies found, using start room")
    
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
        self.room_number = self.current_room.index  # Set room number to current room index
    
        self.state = "game"
    
    # Debug: Check room contents
        print(f"Current room enemies: {len(self.current_room.enemies)}")
        print(f"Current room walls: {len(self.current_room.wall_rects)}")
        for i, enemy in enumerate(self.current_room.enemies):
            print(f"  Enemy {i}: pos={enemy.pos}, alive={enemy.alive}")
    
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
                        self.game_paused = not self.game_paused
                    elif self.state in ["menu", "hub"]:
                        self.state = "menu"
                
                if event.key == pygame.K_h and self.state == "game":
                    self.return_to_hub()
                    return
                
                # Debug key
                if event.key == pygame.K_F3 and self.debug:
                    self.debug = not self.debug
                
                # Level up selection
                if self.state == "game" and self.level_system and self.level_system.showing_upgrades:
                    if event.key in [pygame.K_1, pygame.K_2, pygame.K_3]:
                        upgrade_index = event.key - pygame.K_1
                        if upgrade_index < len(self.level_system.available_upgrades):
                            upgrade_name = self.level_system.apply_upgrade(self.player, upgrade_index)
                            if upgrade_name:
                                self.player.level_up_effect_timer = 2.0
        
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
                        bullet.alive = False
                        if died:
                            self.kill_count += 1
                        break
        
        # Update current room
        if self.current_room and self.player:
            for result in self.current_room.update(self.player, dt):
                if result[0] == "xp":
                    if self.level_system.add_xp(result[1]):
                        # Player leveled up
                        pass
                elif result[0] == "shard":
                    # Shards are collected immediately during run
                    pass
            
            # Keep player in bounds
            self.current_room.keep_player_in_bounds(self.player)
    
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
            
            # Debug info
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
            chest.draw_at_position(self.screen, (int(screen_pos.x), int(screen_pos.y)))
        
        # Draw bullets
        for bullet in self.bullets:
            screen_pos = self.camera.apply_pos(bullet.pos)
            bullet.draw_at_position(self.screen, (int(screen_pos.x), int(screen_pos.y)))
        
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
    
    # Draw UI
        self._draw_game_ui()
    
    def _draw_game_ui(self):
        """Draw clean game UI elements"""
        # Top-right corner stats
        stats = [
            f"Room: {self.room_number + 1}",
            f"Kills: {self.kill_count}",
        ]
        
        if self.level_system:
            stats.append(f"Level: {self.level_system.player_level}")
            xp_progress = self.level_system.xp / self.level_system.xp_to_next_level
            stats.append(f"XP: {int(xp_progress * 100)}%")
        
        for i, stat in enumerate(stats):
            stat_text = self.font.render(stat, True, (255, 255, 255))
            self.screen.blit(stat_text, (WIDTH - stat_text.get_width() - 20, 20 + i * 40))
        
        # Controls hint at bottom
        controls = "WASD: Move | Mouse: Aim/Shoot | ESC: Pause | H: Hub"
        controls_text = self.font.render(controls, True, (150, 150, 150))
        self.screen.blit(controls_text, (WIDTH//2 - controls_text.get_width()//2, HEIGHT - 40))
    
    def _draw_debug_info(self):
        """Draw debug information"""
        debug_info = [
            f"State: {self.state}",
            f"Player: {self.player.pos if self.player else 'None'}",
            f"Camera: {self.camera.camera}",
            f"Current Room: {self.current_room.index if self.current_room else 'None'}",
            f"Enemies: {len(self.current_room.enemies) if self.current_room else 0}",
            f"Bullets: {len(self.bullets)}",
            f"Time: {self.time_elapsed:.1f}s",
            f"FPS: {int(self.clock.get_fps())}"
        ]
        
        for i, info in enumerate(debug_info):
            debug_text = self.font.render(info, True, (255, 100, 100))
            self.screen.blit(debug_text, (10, 10 + i * 30))
    
    def _draw_pause_menu(self):
        """Draw pause menu overlay"""
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        pause_text = self.large_font.render("PAUSED", True, (255, 255, 255))
        self.screen.blit(pause_text, (WIDTH//2 - pause_text.get_width()//2, HEIGHT//2 - 100))
        
        resume_text = self.font.render("Press ESC to resume", True, (200, 200, 200))
        self.screen.blit(resume_text, (WIDTH//2 - resume_text.get_width()//2, HEIGHT//2 + 50))
    
    def _draw_death_screen(self):
        """Draw death screen"""
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        self.screen.blit(overlay, (0, 0))
        
        death_text = self.large_font.render("THE FORGE FADES...", True, (255, 50, 50))
        self.screen.blit(death_text, (WIDTH//2 - death_text.get_width()//2, HEIGHT//2 - 100))
        
        options = [
            "Press ENTER to return to Hub",
            "Press ESC for Main Menu"
        ]
        
        for i, option in enumerate(options):
            option_text = self.font.render(option, True, (200, 200, 100))
            self.screen.blit(option_text, (WIDTH//2 - option_text.get_width()//2, 
                                         HEIGHT//2 + 100 + i * 50))
    
    def run(self):
        """Main game loop"""
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            
            self.update(dt)
            self.draw()
            
            if pygame.time.get_ticks() % 60000 < 16:
                self.save_game()
        
        self.save_game()
        pygame.quit()