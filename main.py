import pygame, sys, random
from core.settings import *
from core.helpers import spawn_position_outside_screen, random_point_in_arena, circle_hit
from entities.player import Player
from entities.enemy import Enemy
from entities.chest import Chest
from entities.weapon import Weapon, weapon_pool

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Echoes of Starforge")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 24)

    # Player spawns with basic pistol
    player = Player(WIDTH//2, HEIGHT//2)
    player.weapon = Weapon("Basic Pistol","ranged",20,5,500,1.2)

    bullets = []
    melees = []
    enemies = []
    chests = []

    enemy_spawn_acc = 0
    chest_timer = CHEST_SPAWN_INTERVAL

    running = True
    while running:
        dt = clock.tick(FPS)/1000
        keys = pygame.key.get_pressed()
        pressed_e = False

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            if e.type == pygame.KEYDOWN and e.key == pygame.K_e:
                pressed_e = True

        # Spawn enemies
        enemy_spawn_acc += dt * ENEMY_SPAWN_PER_SEC
        while enemy_spawn_acc >= 1:
            enemy_spawn_acc -= 1
            enemies.append(Enemy(spawn_position_outside_screen()))

        # Spawn chests
        chest_timer -= dt
        if chest_timer <= 0:
            chest_timer = CHEST_SPAWN_INTERVAL
            item = random.choice(weapon_pool)
            chests.append(Chest(random_point_in_arena(), item))

        # Update entities
        player.update(dt, bullets, melees, keys, pressed_e, chests)
        for b in bullets: b.update(dt)
        for m in melees: m.update(dt, enemies)
        for e in enemies: e.update(dt, player.pos)
        for c in chests:
            if c.opened and c.floating_pickup:
                c.floating_pickup.update(dt)

            # pickup check
            if c.floating_pickup and (player.pos - c.floating_pickup.pos).length() < PICKUP_RANGE and pressed_e:
                player.weapon = c.floating_pickup.item
                c.floating_pickup.active = False

        # Bullet -> enemy collisions
        for b in bullets:
            for e in enemies:
                if e.alive and circle_hit(b.pos, BULLET_RADIUS, e.pos, ENEMY_RADIUS):
                    e.take_damage(b.damage)
                    b.alive = False

        # Clean up dead entities
        bullets = [b for b in bullets if b.alive]
        melees = [m for m in melees if m.alive]
        enemies = [e for e in enemies if e.alive]
        chests = [c for c in chests if not (c.opened and c.floating_pickup and not c.floating_pickup.active)]

        # Draw
        screen.fill(BG)
        for c in chests: c.draw(screen)
        for b in bullets: b.draw(screen)
        for m in melees: m.draw(screen)
        for e in enemies: e.draw(screen)
        player.draw(screen)

        # HUD
        if player.weapon:
            t = font.render(f"Weapon: {player.weapon.name}", True, (255, 255, 255))
            screen.blit(t, (10, 10))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()