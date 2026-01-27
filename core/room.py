# core/room.py
import pygame
import random
import math
from core.settings import *
from entities.enemy import Enemy, XPPickup, ShardPickup
from entities.chest import Chest
from entities.weapon import weapon_pool

class Room:
    def __init__(self, index, grid_x, grid_y, room_type="normal"):
        self.index = index
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.room_type = room_type
        self.connections = []
        
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
        
        self.visited = False
        
        if room_type == "start":
            self.cleared = True
            self.visited = True
        
        # Generate room contents immediately
        self.generate_contents()
    
    def generate_contents(self, difficulty=1):
        self.wall_rects.clear()
        
        # Create walls
        border = TILE_SIZE // 2
        
        # Top wall
        for x in range(0, self.width, TILE_SIZE):
            self.wall_rects.append(pygame.Rect(
                self.pixel_x + x, 
                self.pixel_y, 
                TILE_SIZE, 
                border
            ))
        
        # Bottom wall
        for x in range(0, self.width, TILE_SIZE):
            self.wall_rects.append(pygame.Rect(
                self.pixel_x + x, 
                self.pixel_y + self.height - border, 
                TILE_SIZE, 
                border
            ))
        
        # Left wall
        for y in range(0, self.height, TILE_SIZE):
            self.wall_rects.append(pygame.Rect(
                self.pixel_x, 
                self.pixel_y + y, 
                border, 
                TILE_SIZE
            ))
        
        # Right wall
        for y in range(0, self.height, TILE_SIZE):
            self.wall_rects.append(pygame.Rect(
                self.pixel_x + self.width - border, 
                self.pixel_y + y, 
                border, 
                TILE_SIZE
            ))
        
        # Generate enemies based on room type
        if self.room_type == "enemy" or self.room_type == "normal":
            num_enemies = random.randint(3, 5)
            for _ in range(num_enemies):
                pos = self._get_random_position_in_room()
                enemy = Enemy(pos)
                self.enemies.append(enemy)
            print(f"Room {self.index}: Generated {num_enemies} enemies at positions relative to screen")
        
        elif self.room_type == "boss":
            # Boss room - boss in center of screen
            pos = pygame.Vector2(self.width // 2, self.height // 2)
            boss = Enemy(pos, "boss")
            boss.max_hp = 300
            boss.hp = boss.max_hp
            boss.radius = 40
            boss.speed = 100
            boss.damage = 40
            boss.xp_drop = 100
            boss.shard_drop = 1
            self.enemies.append(boss)
            self.has_boss = True
            print(f"Room {self.index}: Generated boss at screen center {pos}")
        
        elif self.room_type == "treasure":
            num_chests = random.randint(1, 3)
            for _ in range(num_chests):
                pos = self._get_random_position_in_room()
                self.chests.append(Chest(pos, random.choice(weapon_pool())))
            print(f"Room {self.index}: Generated {num_chests} chests")
        
        # Normal rooms can have chests too
        if self.room_type == "normal" and random.random() < 0.4:
            pos = self._get_random_position_in_room()
            self.chests.append(Chest(pos, random.choice(weapon_pool())))
    
    def _get_random_position_in_room(self) -> pygame.Vector2:
        """Get a random position inside the room, away from walls"""
        margin = ROOM_MARGIN
        x = random.uniform(
            self.pixel_x + margin, 
            self.pixel_x + self.width - margin
        )
        y = random.uniform(
            self.pixel_y + margin, 
            self.pixel_y + self.height - margin
        )
        return pygame.Vector2(x, y)
    
    def update(self, player, dt):
        # Update melee attacks
        for melee in self.melees[:]:
            melee.update(dt)
            if not melee.active:
                self.melees.remove(melee)
        
        # Update enemies
        for enemy in self.enemies[:]:
            enemy.update(dt, player, self)
            if not enemy.alive:
                self.enemies.remove(enemy)
                # Add XP pickup when enemy dies
                self.xp_pickups.append(XPPickup(enemy.pos.copy(), enemy.xp_drop))
                if enemy.shard_drop > 0:
                    self.shard_pickups.append(ShardPickup(enemy.pos.copy(), enemy.shard_drop))
        
        # Update XP pickups
        for xp in self.xp_pickups[:]:
            collected = xp.update(dt, player)
            if collected:
                self.xp_pickups.remove(xp)
                yield "xp", xp.amount
            elif not xp.active:
                self.xp_pickups.remove(xp)
        
        # Update shard pickups
        for shard in self.shard_pickups[:]:
            collected = shard.update(dt, player)
            if collected:
                self.shard_pickups.remove(shard)
                yield "shard", shard.amount
            elif not shard.active:
                self.shard_pickups.remove(shard)
        
        # Check if room is cleared
        if not self.cleared and self.room_type != "start":
            if len(self.enemies) == 0:
                self.cleared = True
    
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
        """Keep player within room bounds"""
        player.pos.x = max(self.pixel_x + PLAYER_RADIUS * 2, 
                          min(player.pos.x, self.pixel_x + self.width - PLAYER_RADIUS * 2))
        player.pos.y = max(self.pixel_y + PLAYER_RADIUS * 2, 
                          min(player.pos.y, self.pixel_y + self.height - PLAYER_RADIUS * 2))