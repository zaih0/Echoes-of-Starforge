# core/game_manager.py - COMPLETE UPDATED VERSION
import pygame
import json
import os
from core.settings import WIDTH, HEIGHT, FPS, GRID_SIZE, PLAYER_RADIUS
from core.menu import MainMenu
from core.hub import Hub
from core.dungeon_generator import DungeonGenerator
from core.levelup import LevelUpSystem
from core.camera import Camera
from entities.player import Player
from entities.weapon import starter_weapon, weapon_pool
from entities.charm import get_random_charm, charm_pool
from entities.chest import FloatingPickup
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

        # Floor transition banner state
        self.level_banner_timer = 0.0
        self.level_banner_text = ""
        self.level_banner_subtext = ""
        
        # Font for UI
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
        """Save hub data and, if a run is active, the full run state."""
        data = {}

        # --- Hub / skill-tree ---
        if self.hub:
            st = self.hub.skill_tree
            data["shards"] = st.shards
            data["total_shards"] = st.total_shards_earned
            data["skills"] = {
                name: skill["level"] for name, skill in st.skills.items()
            }

        # --- Active run (only when player is alive) ---
        if self.player and self.player.hp > 0 and self.current_room:
            data["run"] = {
                "current_level": self.current_level,
                "kill_count": self.kill_count,
                "time_elapsed": self.time_elapsed,
                "player": {
                    "hp": self.player.hp,
                    "max_hp": self.player.max_hp,
                    "speed": self.player.speed,
                    "damage_multiplier": self.player.damage_multiplier,
                    "fire_rate_multiplier": self.player.fire_rate_multiplier,
                    "crit_chance": self.player.crit_chance,
                    "life_steal": self.player.life_steal,
                    "health_regen": self.player.health_regen,
                    "damage_reduction": self.player.damage_reduction,
                    "multi_shot": self.player.multi_shot,
                    "bullet_speed_multiplier": self.player.bullet_speed_multiplier,
                    "bullet_pierce": self.player.bullet_pierce,
                    "player_level": self.player.player_level,
                    "weapon": self.player.weapon.name if self.player.weapon else None,
                    "charms": [
                        {"name": c.name, "stacks": getattr(c, "stacks", 1)}
                        for c in self.player.charms
                    ],
                },
                "level_system": {
                    "xp": self.level_system.xp if self.level_system else 0,
                    "xp_to_next_level": self.level_system.xp_to_next_level if self.level_system else 100,
                    "player_level": self.level_system.player_level if self.level_system else 1,
                },
            }

        with open("save_data.json", "w") as f:
            json.dump(data, f, indent=2)

        self.save_data = data
        if self.menu:
            self.menu.save_exists = "run" in data

    def _clear_run_save(self):
        """Remove saved run state (call on new game or after death)."""
        self.save_data.pop("run", None)
        if os.path.exists("save_data.json"):
            try:
                with open("save_data.json", "r") as f:
                    data = json.load(f)
                data.pop("run", None)
                with open("save_data.json", "w") as f:
                    json.dump(data, f, indent=2)
            except Exception:
                pass
        if self.menu:
            self.menu.save_exists = False
    
    def start_new_game(self):
        """Start a new game session"""
        print("=" * 50)
        print("STARTING NEW GAME")
        print("=" * 50)

        # Wipe any previous run save so Continue is disabled
        self._clear_run_save()

        # Reset per-run state
        self.current_level = 1
        self.level_banner_timer = 0.0
        self.level_banner_text = ""
        self.level_banner_subtext = ""

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
        if self.debug:
            print(f"Current room enemies: {len(self.current_room.enemies)}")
            print(f"Current room walls: {len(self.current_room.wall_rects)}")
            print(f"Current room doors: {len(self.current_room.door_rects)}")
            print("=" * 50)
    
    def continue_game(self):
        """Restore a saved in-progress run."""
        self.load_game()
        run_data = self.save_data.get("run")
        if not run_data:
            # No run saved — fall back to a fresh game
            self.start_new_game()
            return

        print("=" * 50)
        print("CONTINUING SAVED RUN")
        print("=" * 50)

        self.current_level = run_data.get("current_level", 1)
        self.kill_count    = run_data.get("kill_count", 0)
        self.time_elapsed  = run_data.get("time_elapsed", 0.0)
        self.level_banner_timer   = 0.0
        self.level_banner_text    = ""
        self.level_banner_subtext = ""

        # Regenerate the dungeon for this floor level
        self.dungeon = DungeonGenerator(self.current_level)
        self.rooms = self.dungeon.generate(self.current_level)
        self.current_room = self.dungeon.get_start_room()
        self.room_number  = self.current_room.index

        # Build player with hub bonuses, then overwrite with saved stats
        skill_bonuses = self.hub.skill_tree.get_bonuses() if self.hub else {}
        spawn_pos = self.current_room.get_player_spawn_position()
        self.player = Player(spawn_pos.x, spawn_pos.y, skill_bonuses)

        pdata = run_data.get("player", {})
        self.player.hp                   = pdata.get("hp", self.player.hp)
        self.player.max_hp               = pdata.get("max_hp", self.player.max_hp)
        self.player.speed                = pdata.get("speed", self.player.speed)
        self.player.damage_multiplier    = pdata.get("damage_multiplier", self.player.damage_multiplier)
        self.player.fire_rate_multiplier = pdata.get("fire_rate_multiplier", self.player.fire_rate_multiplier)
        self.player.crit_chance          = pdata.get("crit_chance", self.player.crit_chance)
        self.player.life_steal           = pdata.get("life_steal", self.player.life_steal)
        self.player.health_regen         = pdata.get("health_regen", self.player.health_regen)
        self.player.damage_reduction     = pdata.get("damage_reduction", self.player.damage_reduction)
        self.player.multi_shot           = pdata.get("multi_shot", self.player.multi_shot)
        self.player.bullet_speed_multiplier = pdata.get("bullet_speed_multiplier", self.player.bullet_speed_multiplier)
        self.player.bullet_pierce        = pdata.get("bullet_pierce", self.player.bullet_pierce)
        self.player.player_level         = pdata.get("player_level", 1)

        # Restore weapon by name
        weapon_name = pdata.get("weapon")
        if weapon_name:
            all_weapons = [starter_weapon()] + weapon_pool()
            matched = next((w for w in all_weapons if w.name == weapon_name), None)
            self.player.weapon = matched if matched else starter_weapon()
        else:
            self.player.weapon = starter_weapon()

        # Restore charms — apply each stack individually to rebuild all stat effects
        for charm_data in pdata.get("charms", []):
            stacks = charm_data.get("stacks", 1)
            for _ in range(stacks):
                pool = charm_pool()
                match = next((c for c in pool if c.name == charm_data["name"]), None)
                if match:
                    self.player.add_charm(match)

        # Restore level-up system
        self.level_system = LevelUpSystem()
        lsdata = run_data.get("level_system", {})
        self.level_system.xp              = lsdata.get("xp", 0)
        self.level_system.xp_to_next_level = lsdata.get("xp_to_next_level", 100)
        self.level_system.player_level    = lsdata.get("player_level", 1)
        self.player.player_level          = self.level_system.player_level

        self.bullets = []
        self.state   = "game"
        print(f"Loaded: Floor {self.current_level}, HP {self.player.hp}/{self.player.max_hp}, Weapon: {self.player.weapon.name}")
        print(f"Charms: {[c.name for c in self.player.charms]}")
        print("=" * 50)
    
    def return_to_hub(self):
        """Return to hub: award shards, save or clear run depending on outcome."""
        shards_earned = self.kill_count // 10 if self.kill_count else 0
        player_alive = self.player and self.player.hp > 0

        if shards_earned > 0 and self.hub:
            self.hub.skill_tree.shards += shards_earned
            self.hub.skill_tree.total_shards_earned += shards_earned

        if player_alive:
            # Mid-run retreat — preserve the run so the player can Continue
            self.save_game()
        else:
            # Death — erase the run save and persist hub data only
            self._clear_run_save()
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
                self.save_game()
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
                        return
                    elif self.state == "dead":
                        # From death screen, go to main menu
                        self.state = "menu"
                        return
                
                # Add M key to go to main menu from pause screen
                if event.key == pygame.K_m and self.state == "game" and self.game_paused:
                    self.save_game()   # preserve the run
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
        
        elif self.state == "game" and not self.game_paused and not (self.level_system and self.level_system.showing_upgrades):
            self._update_game(dt, events)
            
            # Check if player died
            if self.player and self.player.hp <= 0:
                self.state = "dead"
        
        elif self.state == "dead":
            self._update_death_screen(events)
    
    def _update_game(self, dt, events):
        """Update game gameplay"""
        self.time_elapsed += dt

        # Update floor banner countdown
        if self.level_banner_timer > 0:
            self.level_banner_timer -= dt

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
        
        # Handle chest + dropped ground pickups separately
        if self.current_room and self.player:
            collectible_pickups = []

            # Chest-contained pickups
            for chest in self.current_room.chests:
                if chest.pickup and chest.pickup.active and not chest.pickup.collected:
                    collectible_pickups.append((chest.pickup, "chest"))

            # Room dropped pickups (e.g. old weapon after swap)
            for pickup in self.current_room.ground_pickups[:]:
                if pickup and pickup.active and not pickup.collected:
                    collectible_pickups.append((pickup, "ground"))

            for pickup, source in collectible_pickups:
                distance = (self.player.pos - pickup.pos).length()
                if distance < 50 and pickup.can_be_collected():
                    if pickup.collect():
                        dropped_item = self._apply_item_to_player(pickup.item)
                        print(f"Collected: {pickup.item.name}")

                        # If weapon swapped, drop old weapon where player stands so they can swap back
                        if dropped_item and hasattr(dropped_item, "type") and dropped_item.type == "weapon":
                            dropped_pickup = FloatingPickup(self.player.pos.copy(), dropped_item)
                            self.current_room.ground_pickups.append(dropped_pickup)

                        # Clean up consumed ground pickup entries
                        if source == "ground" and pickup in self.current_room.ground_pickups:
                            self.current_room.ground_pickups.remove(pickup)
        
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

        # Boss stair rule: moving through the bottom boss door always advances floor
        if self.current_room.room_type == "boss" and self.current_room.cleared and direction == (1, 0):
            self._generate_next_level(direction)
            return
        
        # Debug output only when debug mode is on
        if self.debug:
            print(f"Attempting to move from room {self.current_room.index} at ({self.current_room.grid_x},{self.current_room.grid_y})")
            print(f"Direction: {direction}")
            print(f"New grid position: ({new_grid_x},{new_grid_y})")
        
        # Check if new position is within grid bounds
        if new_grid_x < 0 or new_grid_x >= GRID_SIZE or new_grid_y < 0 or new_grid_y >= GRID_SIZE:
            if self.current_room.room_type == "boss" and self.current_room.cleared:
                self._generate_next_level(direction)
            elif self.debug:
                print(f"Cannot move: out of bounds ({new_grid_x}, {new_grid_y})")
            return
        
        # Get the adjacent room
        adjacent_room = self.dungeon.get_room_at(new_grid_x, new_grid_y)
        
        if adjacent_room:
            if self.debug:
                print(f"Moving to room {adjacent_room.index} at ({adjacent_room.grid_x},{adjacent_room.grid_y})")
                print(f"Room type: {adjacent_room.room_type}")
            
            # Update current room
            self.current_room = adjacent_room
            self.room_number = self.current_room.index
            
            # Position player near the door they came from
            self._position_player_at_door((-direction[0], -direction[1]))
            
            # Clear bullets when changing rooms
            self.bullets.clear()
            
            # Mark room as visited
            self.current_room.visited = True
            
            if self.debug:
                print(f"Player positioned at: {self.player.pos}")
        else:
            if self.current_room.room_type == "boss" and self.current_room.cleared:
                self._generate_next_level(direction)
            elif self.debug:
                print(f"No room at grid position ({new_grid_x}, {new_grid_y})")
    
    def _position_player_at_door(self, from_direction):
        """Position player near the door they entered from"""
        if not self.player or not self.current_room:
            return
        
        # Get the door rect for the direction we came from
        door_rect = self.current_room.door_rects.get(from_direction)
        
        if door_rect:
            # Position player just inside the door, facing into the room
            offset = 30 + PLAYER_RADIUS
            
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
            if self.debug:
                print(f"Positioned player at door: {from_direction} -> {self.player.pos}")
        else:
            # Fallback to center if no door found
            if self.debug:
                print(f"WARNING: No door found for direction {from_direction}, positioning at center")
            self.player.pos = pygame.Vector2(WIDTH // 2, HEIGHT // 2)
    
    def _generate_next_level(self, direction):
        """Generate the next dungeon floor after the boss is defeated"""
        defeated_floor = self.current_level
        self.current_level += 1
        print(f"[FLOOR ADVANCE] Entering Floor {self.current_level}")

        self.dungeon = DungeonGenerator(self.current_level)
        self.rooms = self.dungeon.generate(self.current_level)

        self.current_room = self.dungeon.get_start_room()

        # Do not send player back to tutorial start: convert start room into an empty treasure room
        self.current_room.room_type = "treasure"
        self.current_room.enemies.clear()
        self.current_room.chests.clear()
        self.current_room.xp_pickups.clear()
        self.current_room.shard_pickups.clear()
        self.current_room.ground_pickups.clear()
        self.current_room.melees.clear()
        self.current_room.cleared = True
        for direction_key in self.current_room.door_open.keys():
            self.current_room.door_open[direction_key] = True

        self.current_room.visited = True
        self.room_number = self.current_room.index

        self.player.pos = self.current_room.get_player_spawn_position()
        self.bullets.clear()

        self.level_banner_timer = 3.0
        self.level_banner_text = f"FLOOR  {self.current_level}"
        self.level_banner_subtext = self._get_boss_defeat_line(defeated_floor)

        # Auto-save on each new floor so Continue works after a boss kill
        self.save_game()

    def _get_boss_defeat_line(self, defeated_floor):
        """Return short story text after a boss defeat."""
        lines = [
            "A forge-warden falls. The path cracks open.",
            "Another shard-song fades into silence.",
            "The vault remembers your name now.",
            "Star-iron cools. The next chamber wakes.",
            "You break the echo, not the will behind it.",
            "The anvil hums deeper below.",
            "A sealed gate yields to your fire.",
            "The dark between stars leans closer."
        ]
        return f"Floor {defeated_floor} Cleared — {lines[(defeated_floor - 1) % len(lines)]}"

    def _apply_item_to_player(self, item):
        """Apply collected item to player"""
        if not self.player:
            return None
        
        # Check item type and apply accordingly
        if hasattr(item, 'type'):
            if item.type == "weapon":
                old_weapon = self.player.weapon
                self.player.weapon = item
                print(f"Equipped new weapon: {item.name}")
                return old_weapon
            elif item.type == "charm":
                # Add charm to player
                self.player.add_charm(item)
        return None
    
    def _update_death_screen(self, events):
        """Update death screen"""
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.return_to_hub()
                elif event.key == pygame.K_ESCAPE:
                    self._clear_run_save()
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

            # Draw UI elements (health, XP, equipment, room info) above the game world
            self._draw_game_ui()

            # Floor transition banner
            if self.level_banner_timer > 0:
                self._draw_level_banner()

            # Draw start room tutorial (suppressed while paused so it doesn't bleed through)
            if self.current_room and self.current_room.room_type == "start" and not self.game_paused:
                self._draw_start_room_tutorial()

            # Level-up card selection (drawn above game, below pause)
            if self.level_system and self.level_system.showing_upgrades:
                self.level_system.draw(self.screen)

            # Pause menu is ALWAYS drawn last so its dark overlay covers everything cleanly
            if self.game_paused:
                self._draw_pause_menu()

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

        # Draw dropped ground pickups (e.g. swapped weapons)
        for pickup in self.current_room.ground_pickups:
            if pickup and pickup.active:
                screen_pos = self.camera.apply_pos(pickup.pos)
                pickup.draw_at_position(self.screen, (screen_pos.x, screen_pos.y))
    
        # Draw player
        if self.player:
            self.player.draw(self.screen, self.camera)
    
    def _draw_game_ui(self):
        """Draw clean game UI elements - REMOVED BOTTOM TEXT"""
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
        
        # REMOVED: All bottom text - tutorial is only in start room
    
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
        
        # Health text
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
            for i, charm in enumerate(self.player.charms[:5]):
                charm_y = charms_y + 30 + (i * 25)
                stack_count = getattr(charm, "stacks", 1)
                stack_suffix = f" x{stack_count}" if stack_count > 1 else ""
                charm_text = self.font_manager.render(
                    f"• {charm.name}{stack_suffix}: {charm.description}",
                    "small", (220, 200, 255)
                )
                self.screen.blit(charm_text, (panel_x + 40, charm_y))
        
        # Show charm count if more than 5
        if self.player and len(self.player.charms) > 5:
            count_text = self.font_manager.render(f"+{len(self.player.charms) - 5} more...", "small", (180, 180, 220))
            self.screen.blit(count_text, (panel_x + 40, charms_y + 30 + (5 * 25)))
    
    def _draw_room_info(self):
        """Draw room information at bottom-left"""
        info_x = 30
        info_y = HEIGHT - 185

        # Background
        pygame.draw.rect(self.screen, (40, 40, 60, 180), (info_x, info_y, 320, 155), border_radius=5)
        pygame.draw.rect(self.screen, (60, 80, 100), (info_x, info_y, 320, 155), 2, border_radius=5)

        # Floor number
        floor_text = self.font_manager.render(f"FLOOR {self.current_level}", "small", (255, 215, 0))
        self.screen.blit(floor_text, (info_x + 20, info_y + 12))

        # Room type
        room_type = self.current_room.room_type.upper()
        room_text = self.font_manager.render(f"ROOM: {room_type}", "normal", (200, 255, 200))
        self.screen.blit(room_text, (info_x + 20, info_y + 42))

        # Enemy count
        enemies_text = self.font_manager.render(f"Enemies: {len(self.current_room.enemies)}", "small", (255, 150, 150))
        self.screen.blit(enemies_text, (info_x + 20, info_y + 88))

        # Cleared status
        cleared_text = self.font_manager.render(
            f"Cleared: {'YES' if self.current_room.cleared else 'NO'}",
            "small", (150, 255, 150) if self.current_room.cleared else (255, 150, 150))
        self.screen.blit(cleared_text, (info_x + 20, info_y + 118))
    
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
        """Draw pause menu overlay — always drawn last so nothing bleeds through."""
        # Full-screen dark scrim
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 210))
        self.screen.blit(overlay, (0, 0))

        # --- Centered panel ---
        panel_w, panel_h = 640, 320
        panel_x = WIDTH  // 2 - panel_w // 2
        panel_y = HEIGHT // 2 - panel_h // 2

        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((15, 20, 35, 240))
        self.screen.blit(panel, (panel_x, panel_y))

        # Gold border
        pygame.draw.rect(self.screen, (255, 215, 0), (panel_x, panel_y, panel_w, panel_h), 3, border_radius=12)
        # Inner subtle border
        pygame.draw.rect(self.screen, (80, 100, 140), (panel_x + 6, panel_y + 6, panel_w - 12, panel_h - 12), 1, border_radius=10)

        cx = WIDTH // 2

        # Title
        pause_surf = self.font_manager.render("PAUSED", "large", (255, 215, 0))
        self.screen.blit(pause_surf, pause_surf.get_rect(centerx=cx, top=panel_y + 28))

        # Divider line
        div_y = panel_y + 28 + pause_surf.get_height() + 18
        pygame.draw.line(self.screen, (80, 100, 140), (panel_x + 30, div_y), (panel_x + panel_w - 30, div_y), 1)

        # Keybind rows
        hints = [
            ("ESC", "Resume game"),
            ("M",   "Return to Main Menu"),
            ("H",   "Retreat to Hub  (shards kept)"),
        ]
        row_y = div_y + 20
        for key, desc in hints:
            key_surf  = self.font_manager.render(f"[{key}]", "normal", (255, 215, 0))
            desc_surf = self.font_manager.render(desc,        "normal", (220, 230, 255))
            key_x  = panel_x + 50
            desc_x = panel_x + 50 + key_surf.get_width() + 24
            self.screen.blit(key_surf,  (key_x,  row_y))
            self.screen.blit(desc_surf, (desc_x, row_y))
            row_y += key_surf.get_height() + 14

        # Floor / kill info footer
        footer_text = self.font_manager.render(
            f"Floor {self.current_level}   |   Kills: {self.kill_count}",
            "small", (140, 160, 200)
        )
        self.screen.blit(footer_text, footer_text.get_rect(centerx=cx, bottom=panel_y + panel_h - 18))
    
    def _draw_level_banner(self):
        """Draw the animated floor transition banner"""
        t = self.level_banner_timer
        if t < 0.5:
            alpha = int(t / 0.5 * 255)
        elif t > 2.7:
            alpha = int((3.0 - t) / 0.3 * 255)
        else:
            alpha = 255
        alpha = max(0, min(255, alpha))

        banner_surf = self.font_manager.render(self.level_banner_text, "large", (255, 215, 0))
        subtext = self.level_banner_subtext or "A new challenge awaits..."
        sub_surf = self.font_manager.render(subtext, "normal", (200, 220, 255))

        pad = 50
        panel_w = max(banner_surf.get_width(), sub_surf.get_width()) + pad * 2
        panel_h = banner_surf.get_height() + sub_surf.get_height() + pad + 20
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((10, 15, 30, min(210, alpha)))
        pygame.draw.rect(panel, (255, 215, 0, min(200, alpha)), panel.get_rect(), 3, border_radius=14)
        panel_rect = panel.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        self.screen.blit(panel, panel_rect)

        banner_surf.set_alpha(alpha)
        sub_surf.set_alpha(alpha)
        self.screen.blit(banner_surf,
                         banner_surf.get_rect(centerx=WIDTH // 2, top=panel_rect.top + 24))
        self.screen.blit(sub_surf,
                         sub_surf.get_rect(centerx=WIDTH // 2,
                                           top=panel_rect.top + banner_surf.get_height() + 36))

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