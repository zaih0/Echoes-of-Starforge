# entities/__init__.py
# This file makes the entities directory a Python package

# Import all classes from enemy.py
from .enemy import Enemy, XPPickup, ShardPickup
from .bullet import Bullet
from .player import Player
from .weapon import Weapon, starter_weapon, weapon_pool
from .chest import Chest, FloatingPickup
from .melee import SwordArc

# Optional: Define what gets imported with "from entities import *"
__all__ = [
    'Enemy', 'XPPickup', 'ShardPickup',
    'Bullet', 'Player', 
    'Weapon', 'starter_weapon', 'weapon_pool',
    'Chest', 'FloatingPickup',
    'SwordArc'
]