# entities/charm.py
class Charm:
    def __init__(self, name, effect, description=""):
        self.name = name
        self.effect = effect
        self.description = description
        self.type = "charm"
        self.rarity = "common"  # common, rare, epic, legendary

def charm_pool():
    return [
        Charm("Forge Heart", 
              lambda p: setattr(p, "max_hp", p.max_hp + 25),
              "+25 Max HP"),
        Charm("Swift Alloy", 
              lambda p: setattr(p, "speed", p.speed * 1.15),
              "+15% Movement Speed"),
        Charm("Overclocked Core", 
              lambda p: setattr(p, "fire_rate_multiplier", getattr(p, "fire_rate_multiplier", 1.0) * 1.2),
              "+20% Fire Rate"),
        Charm("Sharpened Edge", 
              lambda p: setattr(p, "damage_multiplier", getattr(p, "damage_multiplier", 1.0) * 1.15),
              "+15% Damage"),
        Charm("Lucky Charm", 
              lambda p: setattr(p, "crit_chance", getattr(p, "crit_chance", 0.0) + 0.10),
              "+10% Critical Chance"),
        Charm("Regenerative Nanites", 
              lambda p: setattr(p, "health_regen", getattr(p, "health_regen", 0.0) + 2.0),
              "+2 HP/s Regeneration"),
        Charm("Reinforced Plating", 
              lambda p: setattr(p, "damage_reduction", getattr(p, "damage_reduction", 0.0) + 0.15),
              "+15% Damage Reduction"),
        Charm("Vampiric Essence", 
              lambda p: setattr(p, "life_steal", getattr(p, "life_steal", 0.0) + 0.10),
              "+10% Life Steal"),
        Charm("Piercing Rounds", 
              lambda p: setattr(p, "bullet_pierce", getattr(p, "bullet_pierce", 0) + 1),
              "Bullets pierce 1 extra enemy"),
        Charm("Expanded Magazine", 
              lambda p: setattr(p, "multi_shot", getattr(p, "multi_shot", 1) + 1),
              "+1 Projectile per shot"),
    ]

def get_random_charm():
    """Get a random charm, weighted by rarity"""
    pool = charm_pool()
    # 70% common, 20% rare, 8% epic, 2% legendary
    weights = [0.7] * 4 + [0.2] * 3 + [0.08] * 2 + [0.02] * 1
    return random.choices(pool, weights=weights[:len(pool)])[0]