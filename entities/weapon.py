class Weapon:
    def __init__(self, name, wtype, fire_rate, damage,
                 pellets=1, spread=0, speed=700, lifetime=1.2):
        self.name = name
        self.type = wtype
        self.fire_rate = fire_rate
        self.damage = damage
        self.pellets = pellets
        self.spread = spread
        self.speed = speed
        self.lifetime = lifetime

def weapon_pool():
    return [
        Weapon("Rust Pistol","ranged",damage=60, fire_rate=10, speed=720, lifetime=1.4),
        Weapon("Steel Sword","melee",damage=40, fire_rate=1.2, speed=0, lifetime=0),
        Weapon("Steel Sword", "melee", 1.5, 45),
    ]
