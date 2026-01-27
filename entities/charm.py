class Charm:
    def __init__(self, name, effect):
        self.name = name
        self.effect = effect
        self.type = "charm"

def charm_pool():
    return [
        Charm("Forge Heart", lambda p: setattr(p, "max_hp", p.max_hp + 20)),
        Charm("Swift Alloy", lambda p: setattr(p, "speed", p.speed + 30)),
        Charm("Overclocked Core", lambda p: setattr(p, "fire_rate_bonus", p.fire_rate_bonus + 0.3)),
        Charm("Sharpened Edge", lambda p: setattr(p, "melee_bonus", p.melee_bonus + 15)),
    ]
