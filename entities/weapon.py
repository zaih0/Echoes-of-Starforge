# entities/weapon.py
import pygame
import random
from core.settings import BULLET_SPEED, BULLET_RADIUS
from entities.bullet import Bullet

class Weapon:
    def __init__(
        self,
        name,
        wtype,
        fire_rate,
        damage,
        speed=600,
        pellets=1,
        spread=0.0
    ):
        self.name = name
        self.type = "weapon"  # Add type attribute
        self.wtype = wtype          # "ranged" or "melee"
        self.fire_rate = fire_rate
        self.damage = damage
        self.speed = speed
        self.pellets = pellets
        self.spread = spread

    def fire(self, pos: pygame.Vector2, direction: pygame.Vector2 = None) -> Bullet:
        """Fire a bullet from position toward direction"""
        if not direction:
            direction = pygame.Vector2(1, 0)  # Default to right
            
        # Normalize direction
        if direction.length_squared() > 0:
            direction = direction.normalize()
        else:
            direction = pygame.Vector2(1, 0)
        
        # Apply spread
        if self.spread > 0:
            angle = random.uniform(-self.spread, self.spread)
            direction = direction.rotate(angle)
        
        # Create bullet with proper damage
        bullet = Bullet(pos, direction * self.speed, self.damage)
        return bullet


# ------------------------
# Starter weapon (ALWAYS)
# ------------------------
def starter_weapon():
    return Weapon(
        name="Standard Pistol",
        wtype="ranged",
        fire_rate=2.5,   # slow, readable
        damage=20,
        speed=800
    )


# ------------------------
# Loot pool
# ------------------------
def weapon_pool():
    return [
        Weapon("Burst SMG", "ranged", fire_rate=6, damage=12, speed=700, spread=0.12),
        Weapon("Heavy Revolver", "ranged", fire_rate=1.2, damage=45, speed=900),
        Weapon("Forge Blade", "melee", fire_rate=1.1, damage=50),
        Weapon("Twin Daggers", "melee", fire_rate=2.0, damage=25),
        Weapon("Plasma Rifle", "ranged", fire_rate=4.0, damage=30, speed=850),
        Weapon("Shotgun", "ranged", fire_rate=1.5, damage=8, pellets=5, spread=0.2),
    ]