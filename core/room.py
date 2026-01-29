# core/room.py - COMPLETE FIXED VERSION
import pygame
import random
import math
from core.settings import *
from entities.enemy import Enemy, XPPickup, ShardPickup
from entities.chest import Chest
from entities.weapon import weapon_pool
from entities.melee import SwordArc

class Room:
    def __init__(self, index, grid_x, grid_y, room_type="normal"):
        self.index = index
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.room_type = room_type
        self.connections = []  # List of (dx, dy) directions where there are doors
        
        # Each room takes full screen, centered at (0, 0) for single-screen gameplay
        self.width = WIDTH
        self.height = HEIGHT
        self.pixel_x = 0  # Always at (0, 0) - single screen at a time
        self.pixel_y = 0
        
        self.enemies = []
        self.chests = []
        self.melees = []
        self.xp_pickups = []
        self.shard_pickups = []
        self.cleared = False
        self.has_boss = False
        
        self.wall_rects = []
        self.door_rects = {}  # direction -> rect
        self.door_open = {}   # direction -> bool
        
        self.visited = False
        
        if room_type == "start":
            self.cleared = True
            self.visited = True
        
        # Don't generate contents yet - wait for connections to be set
        self.generated = False
    
    def generate_contents(self, difficulty=1):
        """Generate room contents with difficulty scaling"""
        if self.generated:
            return
            
        self.wall_rects.clear()
        self.door_rects.clear()
        self.door_open.clear()
        
        # Create walls with door openings
        border = TILE_SIZE // 2
        
        # DEBUG: Print connections to see what doors should exist
        print(f"Room {self.index} connections: {self.connections}")
        
        # Top wall (with possible door)
        has_top_door = (-1, 0) in self.connections
        if has_top_door:
            print(f"Room {self.index} has top door")
        for x in range(0, self.width, TILE_SIZE):
            if has_top_door and abs(x - self.width // 2) < DOOR_WIDTH // 2:
                continue  # Skip wall where door is
            self.wall_rects.append(pygame.Rect(
                self.pixel_x + x, 
                self.pixel_y, 
                TILE_SIZE, 
                border
            ))
        
        # Bottom wall (with possible door)
        has_bottom_door = (1, 0) in self.connections
        if has_bottom_door:
            print(f"Room {self.index} has bottom door")
        for x in range(0, self.width, TILE_SIZE):
            if has_bottom_door and abs(x - self.width // 2) < DOOR_WIDTH // 2:
                continue
            self.wall_rects.append(pygame.Rect(
                self.pixel_x + x, 
                self.pixel_y + self.height - border, 
                TILE_SIZE, 
                border
            ))
        
        # Left wall (with possible door)
        has_left_door = (0, -1) in self.connections
        if has_left_door:
            print(f"Room {self.index} has left door")
        for y in range(0, self.height, TILE_SIZE):
            if has_left_door and abs(y - self.height // 2) < DOOR_WIDTH // 2:
                continue
            self.wall_rects.append(pygame.Rect(
                self.pixel_x, 
                self.pixel_y + y, 
                border, 
                TILE_SIZE
            ))
        
        # Right wall (with possible door)
        has_right_door = (0, 1) in self.connections
        if has_right_door:
            print(f"Room {self.index} has right door")
        for y in range(0, self.height, TILE_SIZE):
            if has_right_door and abs(y - self.height // 2) < DOOR_WIDTH // 2:
                continue
            self.wall_rects.append(pygame.Rect(
                self.pixel_x + self.width - border, 
                self.pixel_y + y, 
                border, 
                TILE_SIZE
            ))
        
        # Create door rects - FIXED: Use correct coordinates
        if has_top_door:
            door_rect = pygame.Rect(
                self.pixel_x + self.width // 2 - DOOR_WIDTH // 2,
                self.pixel_y,
                DOOR_WIDTH,
                DOOR_HEIGHT
            )
            self.door_rects[(-1, 0)] = door_rect
            # Start room doors are open from beginning, others closed until cleared
            self.door_open[(-1, 0)] = (self.room_type == "start") or self.cleared
            print(f"Created top door at {door_rect}")
        
        if has_bottom_door:
            door_rect = pygame.Rect(
                self.pixel_x + self.width // 2 - DOOR_WIDTH // 2,
                self.pixel_y + self.height - DOOR_HEIGHT,
                DOOR_WIDTH,
                DOOR_HEIGHT
            )
            self.door_rects[(1, 0)] = door_rect
            self.door_open[(1, 0)] = (self.room_type == "start") or self.cleared
            print(f"Created bottom door at {door_rect}")
        
        if has_left_door:
            door_rect = pygame.Rect(
                self.pixel_x,
                self.pixel_y + self.height // 2 - DOOR_WIDTH // 2,
                DOOR_HEIGHT,
                DOOR_WIDTH
            )
            self.door_rects[(0, -1)] = door_rect
            self.door_open[(0, -1)] = (self.room_type == "start") or self.cleared
            print(f"Created left door at {door_rect}")
        
        if has_right_door:
            door_rect = pygame.Rect(
                self.pixel_x + self.width - DOOR_HEIGHT,
                self.pixel_y + self.height // 2 - DOOR_WIDTH // 2,
                DOOR_HEIGHT,
                DOOR_WIDTH
            )
            self.door_rects[(0, 1)] = door_rect
            self.door_open[(0, 1)] = (self.room_type == "start") or self.cleared
            print(f"Created right door at {door_rect}")
        
        print(f"Room {self.index} created {len(self.door_rects)} doors")
        
        # Generate enemies based on room type
        if self.room_type == "enemy" or self.room_type == "normal":
            num_enemies = random.randint(3, 5) + difficulty  # Scale with difficulty
            for _ in range(num_enemies):
                pos = self._get_random_position_in_room()
                enemy = Enemy(pos)
                
                # Scale enemy stats with difficulty
                enemy.max_hp = int(ENEMY_MAX_HP * (1 + (difficulty - 1) * 0.2))
                enemy.hp = enemy.max_hp
                enemy.damage = int(ENEMY_DAMAGE * (1 + (difficulty - 1) * 0.1))
                enemy.xp_drop = int(ENEMY_XP_DROP * (1 + (difficulty - 1) * 0.1))
                
                self.enemies.append(enemy)
        
        elif self.room_type == "boss":
            # Boss room - boss in center of screen
            pos = pygame.Vector2(self.width // 2, self.height // 2)
            boss = Enemy(pos, "boss")
            boss.max_hp = int(BOSS_MAX_HP * (1 + (difficulty - 1) * 0.3))
            boss.hp = boss.max_hp
            boss.radius = BOSS_RADIUS
            boss.speed = BOSS_SPEED
            boss.damage = int(BOSS_DAMAGE * (1 + (difficulty - 1) * 0.2))
            boss.xp_drop = int(BOSS_XP_DROP * (1 + (difficulty - 1) * 0.2))
            boss.shard_drop = BOSS_SHARD_DROP
            self.enemies.append(boss)
            self.has_boss = True
        
        elif self.room_type == "treasure":
            num_chests = random.randint(1, 3)
            for _ in range(num_chests):
                pos = self._get_random_position_in_room()
                self.chests.append(Chest(pos, random.choice(weapon_pool())))
        
        # Normal rooms can have chests too
        if self.room_type == "normal" and random.random() < 0.4:
            pos = self._get_random_position_in_room()
            self.chests.append(Chest(pos, random.choice(weapon_pool())))
        
        self.generated = True

    def _get_random_position_in_room(self):
        """Get a random position within the room, avoiding walls and center"""
        margin = 100  # Keep away from walls
        x = random.randint(margin, self.width - margin)
        y = random.randint(margin, self.height - margin)
        
        # Avoid center area (where player might spawn)
        center_margin = 150
        center_x, center_y = self.width // 2, self.height // 2
        
        # If position is too close to center, adjust it
        if abs(x - center_x) < center_margin and abs(y - center_y) < center_margin:
            # Move to one of the quadrants
            if x < center_x:
                x = random.randint(margin, center_x - center_margin)
            else:
                x = random.randint(center_x + center_margin, self.width - margin)
            
            if y < center_y:
                y = random.randint(margin, center_y - center_margin)
            else:
                y = random.randint(center_y + center_margin, self.height - margin)
        
        return pygame.Vector2(x, y)

    def update(self, player, dt, keys):
        """Update room state"""
        results = []
        
        # Update enemies - FIXED: Call with correct parameters (player, dt, walls)
        for enemy in self.enemies[:]:
            enemy.update(player, dt, self.wall_rects)
            
            # Check if enemy died
            if not enemy.alive:
                # Drop XP
                xp_pickup = XPPickup(enemy.pos.copy(), enemy.xp_drop)
                self.xp_pickups.append(xp_pickup)
                
                # Drop shard if boss
                if enemy.enemy_type == "boss":
                    shard_pickup = ShardPickup(enemy.pos.copy(), enemy.shard_drop)
                    self.shard_pickups.append(shard_pickup)
                    results.append(("shard", enemy.shard_drop))
                
                self.enemies.remove(enemy)
                results.append(("xp", enemy.xp_drop))
        
        # Update XP pickups - FIXED: Call with correct parameters (player, dt)
        for xp_pickup in self.xp_pickups[:]:
            collected = xp_pickup.update(player, dt)
            if collected:
                results.append(("xp", xp_pickup.amount))
                self.xp_pickups.remove(xp_pickup)
        
        # Update shard pickups - FIXED: Call with correct parameters (player, dt)
        for shard_pickup in self.shard_pickups[:]:
            collected = shard_pickup.update(player, dt)
            if collected:
                results.append(("shard", shard_pickup.amount))
                self.shard_pickups.remove(shard_pickup)
        
        # Update chests
        for chest in self.chests:
            chest.update(player, dt, keys)
        
        # Check if all enemies are dead to clear room and open doors
        if not self.cleared and len(self.enemies) == 0:
            self.cleared = True
            # Open all doors
            for direction in self.door_rects.keys():
                self.door_open[direction] = True
            print(f"Room {self.index} cleared! Doors opened.")
        
        # Check if player is exiting through a door
        if self.cleared and player:
            for direction, door_rect in self.door_rects.items():
                if self.door_open.get(direction, False):
                    player_rect = pygame.Rect(
                        player.pos.x - PLAYER_RADIUS,
                        player.pos.y - PLAYER_RADIUS,
                        PLAYER_RADIUS * 2,
                        PLAYER_RADIUS * 2
                    )
                    if player_rect.colliderect(door_rect):
                        results.append(("exit", direction))
        
        # Update melee attacks
        for melee in self.melees[:]:
            melee.update(dt)
            if not melee.alive:
                self.melees.remove(melee)
        
        return results

    def draw(self, screen, camera):
        """Draw the room with camera offset"""
        # Draw floor (entire screen since room is at (0, 0))
        floor_rect = pygame.Rect(0, 0, self.width, self.height)
        pygame.draw.rect(screen, FLOOR_COLOR, floor_rect)
        
        # Draw walls
        for wall in self.wall_rects:
            wall_rect = pygame.Rect(
                wall.x,
                wall.y,
                wall.width,
                wall.height
            )
            pygame.draw.rect(screen, WALL_COLOR, wall_rect)
        
        # Draw doors
        if len(self.door_rects) == 0:
            print(f"WARNING: Room {self.index} has 0 doors!")
        else:
            print(f"Room {self.index} drawing {len(self.door_rects)} doors")
            
        for direction, door_rect in self.door_rects.items():
            is_open = self.door_open.get(direction, False)
            is_boss_door = self.has_boss
            
            if is_open:
                color = DOOR_OPEN_COLOR
            elif is_boss_door:
                color = BOSS_DOOR_COLOR
            else:
                color = DOOR_COLOR
            
            # Draw the door rectangle
            pygame.draw.rect(screen, color, door_rect, border_radius=5 if is_open else 0)
            
            # Draw door outline
            pygame.draw.rect(screen, (30, 30, 40), door_rect, 2, border_radius=5 if is_open else 0)
            
            # Draw boss indicator (red triangle)
            if self.has_boss and not is_open:
                # Draw red triangle above boss door
                if direction == (-1, 0):  # Top door
                    points = [
                        (door_rect.centerx, door_rect.top - 15),
                        (door_rect.centerx - 10, door_rect.top - 5),
                        (door_rect.centerx + 10, door_rect.top - 5)
                    ]
                elif direction == (1, 0):  # Bottom door
                    points = [
                        (door_rect.centerx, door_rect.bottom + 15),
                        (door_rect.centerx - 10, door_rect.bottom + 5),
                        (door_rect.centerx + 10, door_rect.bottom + 5)
                    ]
                elif direction == (0, -1):  # Left door
                    points = [
                        (door_rect.left - 15, door_rect.centery),
                        (door_rect.left - 5, door_rect.centery - 10),
                        (door_rect.left - 5, door_rect.centery + 10)
                    ]
                else:  # Right door
                    points = [
                        (door_rect.right + 15, door_rect.centery),
                        (door_rect.right + 5, door_rect.centery - 10),
                        (door_rect.right + 5, door_rect.centery + 10)
                    ]
                
                pygame.draw.polygon(screen, (255, 50, 50), points)
                pygame.draw.polygon(screen, (255, 150, 150), points, 2)
            
            # Draw door open indicator (arrow)
            if is_open:
                # Draw arrow pointing through door
                if direction == (-1, 0):  # Top door
                    arrow_points = [
                        (door_rect.centerx, door_rect.centery - 10),
                        (door_rect.centerx - 8, door_rect.centery + 5),
                        (door_rect.centerx + 8, door_rect.centery + 5)
                    ]
                elif direction == (1, 0):  # Bottom door
                    arrow_points = [
                        (door_rect.centerx, door_rect.centery + 10),
                        (door_rect.centerx - 8, door_rect.centery - 5),
                        (door_rect.centerx + 8, door_rect.centery - 5)
                    ]
                elif direction == (0, -1):  # Left door
                    arrow_points = [
                        (door_rect.centerx - 10, door_rect.centery),
                        (door_rect.centerx + 5, door_rect.centery - 8),
                        (door_rect.centerx + 5, door_rect.centery + 8)
                    ]
                else:  # Right door
                    arrow_points = [
                        (door_rect.centerx + 10, door_rect.centery),
                        (door_rect.centerx - 5, door_rect.centery - 8),
                        (door_rect.centerx - 5, door_rect.centery + 8)
                    ]
                
                pygame.draw.polygon(screen, (255, 255, 255), arrow_points)
    
    def is_point_in_room(self, point):
        """Check if a point is inside this room"""
        return (self.pixel_x <= point.x <= self.pixel_x + self.width and
                self.pixel_y <= point.y <= self.pixel_y + self.height)
    
    def get_player_spawn_position(self):
        """Get spawn position for player - center of screen"""
        return pygame.Vector2(
            self.width // 2,
            self.height // 2
        )
    
    def keep_player_in_bounds(self, player):
        """Keep player within room bounds, but allow exit through open doors"""
        # Check if player is near an open door
        near_open_door = False
        for direction, door_rect in self.door_rects.items():
            if self.door_open.get(direction, False):
                player_rect = pygame.Rect(
                    player.pos.x - PLAYER_RADIUS,
                    player.pos.y - PLAYER_RADIUS,
                    PLAYER_RADIUS * 2,
                    PLAYER_RADIUS * 2
                )
                if player_rect.colliderect(door_rect):
                    near_open_door = True
                    break
        
        # If not near an open door, keep within bounds
        if not near_open_door:
            player.pos.x = max(self.pixel_x + PLAYER_RADIUS * 2, 
                              min(player.pos.x, self.pixel_x + self.width - PLAYER_RADIUS * 2))
            player.pos.y = max(self.pixel_y + PLAYER_RADIUS * 2, 
                              min(player.pos.y, self.pixel_y + self.height - PLAYER_RADIUS * 2))