class Charm:
    def __init__(self, name, effect, value):
        self.name = name
        self.effect = effect
        self.value = value

def charm_pool():
    return [
        Charm("Vital Core", "max_hp", 20),
        Charm("Forge Reflex", "fire_rate", 0.15),
        Charm("Light Frame", "speed", 25),
    ]
