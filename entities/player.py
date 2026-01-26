import pygame, math, random
from entities.bullet import Bullet
from entities.melee import MeleeAttack
from core.settings import PLAYER_RADIUS

class Player:
    def __init__(self, x, y):
        self.pos = pygame.Vector2(x, y)
        self.weapon = None
        self._shoot_cd = 0
        self._muzzle_flash = 0
        self.melees = []

    @property
    def mouse_pos(self):
        return pygame.Vector2(pygame.mouse.get_pos())

    def update(self, dt, bullets, melee_list, keys, pressed_e, chests):
        # movement
        vx = vy = 0
        if keys[pygame.K_w]: vy -=1
        if keys[pygame.K_s]: vy +=1
        if keys[pygame.K_a]: vx -=1
        if keys[pygame.K_d]: vx +=1
        length = math.hypot(vx, vy)
        if length > 0: vx, vy = vx/length, vy/length
        self.pos += pygame.Vector2(vx, vy) * 260 * dt

        # shooting
        self._shoot_cd = max(0, self._shoot_cd - dt)
        self._muzzle_flash = max(0, self._muzzle_flash - dt)
        if pygame.mouse.get_pressed()[0] and self.weapon and self._shoot_cd <= 0 and self.weapon.type=="ranged":
            self.shoot(bullets)
            self._shoot_cd = 1/self.weapon.fire_rate
            self._muzzle_flash = 0.08

        # melee
        if pygame.mouse.get_pressed()[0] and self.weapon and self.weapon.type=="melee" and self._shoot_cd <= 0:
            m = MeleeAttack(self.pos, self.mouse_pos - self.pos, self.weapon)
            melee_list.append(m)
            self._shoot_cd = 1/self.weapon.fire_rate

        # open chest
        if pressed_e:
            for chest in chests:
                if not chest.opened and (chest.pos - self.pos).length() < 46:
                    chest.open()
                    break

    def shoot(self, bullets):
        aim = self.mouse_pos - self.pos
        if aim.length_squared() == 0: return
        base_angle = math.atan2(aim.y, aim.x)
        d = pygame.Vector2(math.cos(base_angle), math.sin(base_angle))
        bullets.append(Bullet(self.pos + d*20, d*self.weapon.speed, self.weapon.lifetime, self.weapon.damage))

    def draw(self, surface):
        # player body
        pygame.draw.circle(surface, (220,220,255), (int(self.pos.x), int(self.pos.y)), PLAYER_RADIUS)
        # aim line
        mp = pygame.mouse.get_pos()
        pygame.draw.line(surface, (120,200,255), (int(self.pos.x), int(self.pos.y)), mp,2)
        # muzzle flash
        if self._muzzle_flash > 0:
            aim = self.mouse_pos - self.pos
            if aim.length_squared()>0:
                d = aim.normalize()
                p = self.pos + d*(PLAYER_RADIUS+10)
                pygame.draw.circle(surface, (255,255,255), (int(p.x), int(p.y)),8,2)
                pygame.draw.circle(surface, (255,240,180), (int(p.x), int(p.y)),6,1)
