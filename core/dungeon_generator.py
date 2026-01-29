# core/dungeon_generator.py - UPDATED
import random
from typing import List
from core.settings import *
from core.room import Room

class DungeonGenerator:
    def __init__(self, level=1):
        self.level = level
        self.rooms: List[Room] = []
        self.room_grid = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.start_room_pos = (GRID_SIZE // 2, 0)  # Start at top
        
    def generate(self, level=1) -> List[Room]:
        self.level = level
        self.rooms = []
        self.room_grid = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        
        # Start room
        start_x, start_y = self.start_room_pos
        start_room = Room(0, start_x, start_y, "start")
        self.rooms.append(start_room)
        self.room_grid[start_y][start_x] = start_room
        
        # Determine number of rooms
        num_rooms = random.randint(MIN_ROOMS, MAX_ROOMS)
        
        # Generate path to boss
        self._generate_path_to_boss(start_x, start_y, num_rooms)
        
        # Add some extra rooms if needed
        if len(self.rooms) < num_rooms:
            self._add_extra_rooms(num_rooms - len(self.rooms))
        
        # Connect rooms (set connections based on grid adjacency)
        self._set_room_connections()
        
        # Generate room contents AFTER connections are set
        for i, room in enumerate(self.rooms):
            room.generate_contents(self.level)
            print(f"Room {i} at ({room.grid_x},{room.grid_y}) type: {room.room_type}, connections: {room.connections}")
        
        # Ensure start room has proper door states
        start_room = self.rooms[0]
        for direction in start_room.door_open:
            start_room.door_open[direction] = True
        
        print(f"Generated {len(self.rooms)} rooms")
        return self.rooms
    
    def _generate_path_to_boss(self, start_x, start_y, num_rooms):
        """Generate a path from start to boss room"""
        current_x, current_y = start_x, start_y
        path_length = random.randint(4, 6)
        
        for i in range(path_length):
            # Move downward (toward boss)
            current_y += 1
            if current_y >= GRID_SIZE:
                current_y = GRID_SIZE - 1
                break
            
            # Create room
            if i == path_length - 1:
                room_type = "boss"
            elif i == 0:
                room_type = "normal"
            else:
                room_type = random.choice(["normal", "enemy", "treasure"])
            
            room = Room(len(self.rooms), current_x, current_y, room_type)
            self.rooms.append(room)
            self.room_grid[current_y][current_x] = room
            
            # Don't set connections here - will be done in _set_room_connections
    
    def _add_extra_rooms(self, num_extra):
        """Add extra rooms branching from existing ones"""
        attempts = 0
        max_attempts = num_extra * 10
        
        while len(self.rooms) < (len(self.rooms) + num_extra) and attempts < max_attempts:
            attempts += 1
            
            # Find existing rooms that have space around them
            possible_parents = []
            for room in self.rooms:
                x, y = room.grid_x, room.grid_y
                # Check all directions
                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    nx, ny = x + dx, y + dy
                    # Check if position is within bounds AND empty
                    if (0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE and 
                        self.room_grid[ny][nx] is None):
                        possible_parents.append((room, dx, dy, nx, ny))
            
            if not possible_parents:
                break
            
            # Pick random parent and direction
            parent, dx, dy, nx, ny = random.choice(possible_parents)
            
            # Determine room type (no boss in branches)
            room_types = ["normal"] * 60 + ["enemy"] * 25 + ["treasure"] * 15
            room_type = random.choice(room_types)
            
            # Create room
            room = Room(len(self.rooms), nx, ny, room_type)
            self.rooms.append(room)
            self.room_grid[ny][nx] = room
    
    def _set_room_connections(self):
        """Set connections between rooms based on grid adjacency"""
        for room in self.rooms:
            x, y = room.grid_x, room.grid_y
            
            # Check all 4 directions for adjacent rooms
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                
                # Check if neighbor is within bounds
                if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                    neighbor = self.room_grid[ny][nx]
                    
                    # If there's a room in this direction, add connection
                    if neighbor is not None:
                        # Add connection to current room
                        if (dx, dy) not in room.connections:
                            room.connections.append((dx, dy))
                        
                        # Add reverse connection to neighbor
                        reverse_dir = (-dx, -dy)
                        if reverse_dir not in neighbor.connections:
                            neighbor.connections.append(reverse_dir)
    
    def get_room_at(self, grid_x, grid_y):
        """Get room at grid coordinates"""
        if 0 <= grid_y < GRID_SIZE and 0 <= grid_x < GRID_SIZE:
            return self.room_grid[grid_y][grid_x]
        return None
    
    def get_start_room(self):
        return self.rooms[0]
    
    def get_boss_room(self):
        for room in self.rooms:
            if room.room_type == "boss":
                return room
        return None