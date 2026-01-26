class Weapon:
    def __init__(self, name, wtype, fire_rate, damage, speed=500):
        self.name = name
        self.type = wtype
        self.fire_rate = fire_rate
        self.damage = damage
        self.speed = speed

def weapon_pool():
    return [
        Weapon("Rust Pistol", "ranged", 2.5, 14),
        Weapon("Burst Rifle", "ranged", 1.4, 26),
        Weapon("Star SMG", "ranged", 5.0, 8),
        Weapon("Forge Blade", "melee", 1.1, 45),
        Weapon("Steel Sword", "melee", 1.5, 40),
    ]
