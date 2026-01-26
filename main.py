import pygame, sys, random
from core.settings import *
from core.helpers import *
from entities.player import Player
from entities.enemy import Enemy
from entities.chest import Chest
from entities.weapon import weapon_pool

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

player = Player(WIDTH//2, HEIGHT//2)
player.weapon = weapon_pool()[0]

bullets, enemies, chests = [], [], []
enemy_timer = 0
chest_timer = CHEST_SPAWN_INTERVAL
paused = False

while True:
    dt = clock.tick(FPS)/1000
    pressed_e = False

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                pygame.quit(); sys.exit()
            if e.key == pygame.K_TAB:
                paused = not paused
            if e.key == pygame.K_e:
                pressed_e = True
            if player.hp <=0:
                if e.key == pygame.K_r:
                    # Reforge
                    player.hp = PLAYER_MAX_HP
                    player.weapon = weapon_pool()[0]
                if e.key == pygame.K_a:
                    # Respawn
                    player.hp = PLAYER_MAX_HP
                    player.pos = pygame.Vector2(WIDTH//2, HEIGHT//2)

    if paused: continue

    keys = pygame.key.get_pressed()
    if player.hp>0:
        player.update(dt, bullets, keys, enemies)

    enemy_timer += dt*ENEMY_SPAWN_PER_SEC
    if enemy_timer>=1:
        enemy_timer=0
        enemies.append(Enemy(spawn_position_outside_screen()))

    chest_timer -= dt
    if chest_timer<=0:
        chest_timer = CHEST_SPAWN_INTERVAL
        chests.append(Chest(random_point_in_arena(), random.choice(weapon_pool())))

    for b in bullets: b.update(dt)
    for e in enemies: e.update(dt, player.pos)

    for b in bullets:
        for e in enemies:
            if circle_hit(b.pos, BULLET_RADIUS, e.pos, ENEMY_RADIUS):
                e.take_damage(b.damage)
                b.alive=False
                break

    bullets=[b for b in bullets if b.alive]
    enemies=[e for e in enemies if e.alive]

    if player.hp>0:
        for e in enemies:
            if (player.pos-e.pos).length() < ENEMY_RADIUS+PLAYER_RADIUS:
                player.hp -= 15*dt
                player.hp = max(player.hp,0)

    for c in chests:
        if pressed_e and not c.opened and (player.pos - c.pos).length() < OPEN_RANGE:
            c.open()
        if c.pickup:
            c.pickup.update(dt)
            if pressed_e and (player.pos - c.pickup.pos).length() < PICKUP_RANGE:
                player.weapon = c.item
                c.pickup.active=False

    chests=[c for c in chests if not (c.pickup and not c.pickup.active)]

    screen.fill(BG)
    for c in chests: c.draw(screen)
    for b in bullets: b.draw(screen)
    for e in enemies: e.draw(screen)
    player.draw(screen)

    # Death overlay
    if player.hp<=0:
        font = pygame.font.Font(None, 40)
        text = font.render("You are down! Press R to Reforge or A to Respawn", True, (255,255,255))
        screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - 20))

    pygame.display.flip()
