import pygame
import math
import sys
import random
from enum import Enum, auto

pygame.init()

W, H = 800, 600
FPS = 60

screen = pygame.display.set_mode((W, H))
clock = pygame.time.Clock()

def lerp(a, b, t):
    return a + (b - a) * t


def distance(a, b):
    return ((a[0] - b[0])**2 + (a[1] - b[1])**2) ** 0.5


def bounce(obj, r=700):
    dx, dy = obj.pos[0], obj.pos[1]
    d = distance((0,0), (dx,dy))
    if d + obj.size > r:
        nx, ny = dx / d, dy / d
        dot = obj.vel[0]*nx + obj.vel[1]*ny
        obj.vel[0] -= 2*dot*nx
        obj.vel[1] -= 2*dot*ny
        obj.pos[0] -= nx * (d + obj.size - r)
        obj.pos[1] -= ny * (d + obj.size - r)


def render_transparent_circle(screen, color, pos, radius, alpha):
    surf = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
    pygame.draw.circle(surf, (*color[:3], alpha), (radius, radius), radius)
    screen.blit(surf, (pos[0] - radius, pos[1] - radius))



class Registry(Enum):
    OBJECT_MODE_STATIC = auto()
    OBJECT_MODE_DYNAMIC = auto()



class Object:
    def __init__(self, pos, vel, color, size, camera, mode = Registry.OBJECT_MODE_DYNAMIC):
        self.camera = camera
        self.pos = list(pos)
        self.vel = list(vel)
        self.color = color
        self.size = size
        self.mode = mode

    def update(self, dt):
        if self.mode == Registry.OBJECT_MODE_DYNAMIC:
            self.pos[0] += self.vel[0] * dt
            self.pos[1] += self.vel[1] * dt

    def render(self, screen):
        pygame.draw.circle(screen, self.color, (self.pos[0] - self.camera.pos[0], self.pos[1] - self.camera.pos[1]), self.size)



class Camera(Object):
    def __init__(self, pos, target):
        super().__init__(pos, [0,0], None, None, None, Registry.OBJECT_MODE_STATIC)
        self.target = target

    def update(self, dt):
        super().update(dt)
        self.pos[0] = lerp(self.pos[0], self.target.pos[0]-W/2, 0.1)
        self.pos[1] = lerp(self.pos[1], self.target.pos[1]-H/2, 0.1)



class Star(Object):
    def __init__(self, pos, parallax_factor, flicker_speed, color, size, camera):
        super().__init__(pos, [0,0], color, size, camera, Registry.OBJECT_MODE_STATIC)
        self.parallax_factor = parallax_factor
        self.flicker_speed = flicker_speed
        self.flicker_i = random.random()*10

    def update(self, dt):
        self.flicker_i += self.flicker_speed * dt

    def render(self, screen):
        x = (self.pos[0] - self.camera.pos[0] * self.parallax_factor) % W
        y = (self.pos[1] - self.camera.pos[1] * self.parallax_factor) % H

        for dy in (-H, 0, H):
            for dx in (-W, 0, W):
                render_x = x + dx
                render_y = y + dy
                if 0 <= render_x <= W and 0 <= render_y <= H:
                    render_transparent_circle(screen, self.color, (render_x, render_y), self.size, 150+(math.sin(self.flicker_i)*100))

class Rift(Object):
    def __init__(self, pos, spawn, camera):
        super().__init__(pos, [0,0], (100,100,255), 0, camera, Registry.OBJECT_MODE_STATIC)
        self.spawn = list(spawn)
        self.spawn_rate = 0.2
        self.spawn_time = self.spawn_rate
        self.wave = 0

    def update(self, dt):
        if len(enemies) == 0 and len(self.spawn) == 0:
            bonus = 0
            if player.health >= 3 + (self.wave // 5 * 3) and self.wave != 0: bonus = 1
            self.wave += 1
            self.spawn = [Enemy([20,20], camera, player, [0,0]) for i in range(self.wave)]
            player.health = 3 + (self.wave // 5 * 3) + bonus

        elif len(self.spawn) > 0:
            if self.spawn_time <= 0:
                enemies.append(self.spawn[-1])
                particles.append(Particle(self.spawn[-1].pos, [0,0], (120,120,255), 1, camera, 0.2, end_alpha=0, end_size=100))
                self.spawn.remove(self.spawn[-1])
                self.spawn_time = self.spawn_rate
            else:
                self.spawn_time -= dt
        if player.health <= 0:
            self.wave -= 2
            enemies.clear()

    def render(self, screen):
        x = self.pos[0] - self.camera.pos[0]
        y = self.pos[1] - self.camera.pos[1]
        for i in range(10):
            size = random.randint(10, 20)
            render_transparent_circle(screen, self.color, (x + random.randint(-10, 10),y + random.randint(-10, 10)), size, random.randint(50,100))



class Particle(Object):
    def __init__(self, pos, vel, color, size, camera, lifetime, end_vel = None, end_color = None, end_size = None, alpha = 255, end_alpha = None):
        super().__init__(pos, vel, color, size, camera)
        self.alpha = alpha
        self.start_alpha = alpha
        self.end_alpha = end_alpha
        self.start_vel = vel
        self.start_color = color
        self.start_size = size
        self.end_vel = end_vel
        self.end_color = end_color
        self.end_size = end_size
        self.lifetime = lifetime
        self.time = 0

    def update(self, dt):
        super().update(dt)
        self.time += dt
        t = min(self.time / self.lifetime, 1)

        if self.end_vel is not None:
            self.vel = [
                lerp(self.start_vel[0], self.end_vel[0], t),
                lerp(self.start_vel[1], self.end_vel[1], t)
            ]
        if self.end_color is not None:
            self.color = (
                lerp(self.start_color[0], self.end_color[0], t),
                lerp(self.start_color[1], self.end_color[1], t),
                lerp(self.start_color[2], self.end_color[2], t)
            )
        if self.end_size is not None:
            self.size = lerp(self.start_size, self.end_size, t)

        if self.end_alpha is not None:
            self.alpha = lerp(self.start_alpha, self.end_alpha, t)

    def render(self, screen):
        render_transparent_circle(screen, self.color, (self.pos[0]-self.camera.pos[0], self.pos[1]-self.camera.pos[1]), self.size, self.alpha)


class Spaceship(Object):
    def __init__(self, pos, speed, color, camera, health = 1, vel = [0,0]):
        super().__init__(pos, vel, color, 5, camera)
        self.angle = 0
        self.speed = speed
        self.health = health
        self.shoot_time = 0
        self.shoot_cooldown = 1

    def update(self, dt):
        super().update(dt)

        self.thrust(self.speed, self.angle, dt)
        self.vel[0] = lerp(self.vel[0], 0, 0.02)
        self.vel[1] = lerp(self.vel[1], 0, 0.02)

    def rotate(self, speed, dt):
        self.angle += speed * dt
        self.angle %= 360

        rad = math.radians(self.angle + 90)
        dx = math.cos(rad) * speed * dt
        dy = math.sin(rad) * speed * dt
        particles.append(Particle(self.pos, [-dx*40, -dy*40], (255,255,255), 3, self.camera, 0.1, end_alpha=0, end_size=0))

    def thrust(self, speed, angle, dt):
        rad = math.radians(angle)
        dx = math.cos(rad) * speed * dt
        dy = math.sin(rad) * speed * dt
        self.vel[0] += dx
        self.vel[1] += dy
        particles.append(Particle((self.pos[0]+(random.random()*2-1), self.pos[1]+(random.random()*2-1)), [-dx*40, -dy*40], (255,255,255), 4, self.camera, 0.2, end_color=(100,0,0), end_size=0))

    def on_death(self):
        particles.append(
            Particle(self.pos, [0, 0], self.color, self.size, camera, 0.2, end_alpha=0, end_size=self.size * 10))


class Player(Spaceship):
    def __init__(self, pos, camera, vel = [0,0]):
        super().__init__(pos, 0, (128, 128, 255), camera, 10, vel)
        self.angle = 0
        self.speeds = [
            [-50, 30, 150],
            [-100, 30, 300]
        ]
        self.speed = self.speeds[0][1]


    def update(self, dt):
        super().update(dt)

        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            self.speed = self.speeds[keys[pygame.K_LCTRL]][2]
        elif keys[pygame.K_s]:
            self.speed = self.speeds[keys[pygame.K_LCTRL]][0]
        else:
            self.speed = self.speeds[keys[pygame.K_LCTRL]][1]
        mouse = pygame.mouse.get_pressed()

        if mouse[0]:
            if self.shoot_time <= 0:
                mx, my = pygame.mouse.get_pos()
                rad = math.atan2(my + self.camera.pos[1] - self.pos[1], mx + self.camera.pos[0] - self.pos[0])
                bullets.append(PlayerBullet(self.pos, [math.cos(rad) * 300 + self.vel[0], math.sin(rad) * 300 + self.vel[1]], self.color, self.size / 2, self.camera, 5))
                particles.append(Particle(self.pos, [0, 0], self.color, self.size, camera, 0.2, end_color=(0, 0, 0), end_size=self.size * 3))
                self.shoot_time = self.shoot_cooldown

        self.shoot_time -= dt

        if keys[pygame.K_a]:
            self.rotate(250, dt)
        if keys[pygame.K_d]:
            self.rotate(-250, dt)

    def render_UI(self, screen):
        for i in range(self.health):
            pygame.draw.circle(screen, (128, 255, 128), (20+(10*i), 20), 4)


class Enemy(Spaceship):
    def __init__(self, pos, camera, target, vel=[0, 0]):
        super().__init__(pos, 0, (255, 100, 100), camera, health=1, vel=vel)
        self.angle = 0
        self.target = target
        self.shoot_time = random.random()*2
        self.offset = random.random()*4
        self.speeds = [150+self.offset, 270+self.offset]
        self.speed = self.speeds[0]

    def update(self, dt):
        super().update(dt)
        self.shoot_cooldown = 1+0.1*len(enemies)

        self.speed = self.speeds[0 if distance(self.pos, self.target.pos) < 200 else 1]

        dx = self.pos[0] - self.target.pos[0]
        dy = self.pos[1] - self.target.pos[1]

        angle = math.degrees(math.atan2(dy, dx)) % 360

        diff = (angle - self.angle) % 360 - 180

        if diff > 5+self.offset:
            self.rotate(250, dt)
        if diff < -5-self.offset:
            self.rotate(-250, dt)

        if self.shoot_time <= 0:
            rad = math.radians(self.angle)
            bullets.append(EnemyBullet(self.pos, [math.cos(rad) * 250 + self.vel[0], math.sin(rad) * 250 + self.vel[1]], (255, 60, 60), self.size / 2, self.camera, 2))
            particles.append(Particle(self.pos, [0, 0], (255, 60, 60), self.size, self.camera, 0.3, end_alpha=0, end_size=self.size * 3))
            self.shoot_time = self.shoot_cooldown

        self.shoot_time -= dt



class Bullet(Object):
    def __init__(self, pos, vel, color, size, camera, lifetime):
        super().__init__(pos, vel, color, size, camera)
        self.lifetime = lifetime
        self.time = 0
        self.collided = 0

    def update(self, dt):
        super().update(dt)
        self.time += dt


class EnemyBullet(Bullet):
    def __init__(self, pos, vel, color, size, camera, lifetime):
        super().__init__(pos, vel, color, size, camera, lifetime)

    def update(self, dt):
        super().update(dt)
        if distance(self.pos, player.pos) < self.size+player.size:
            self.collided = True
            player.health -= 1


class PlayerBullet(Bullet):
    def __init__(self, pos, vel, color, size, camera, lifetime):
        super().__init__(pos, vel, color, size, camera, lifetime)

    def update(self, dt):
        super().update(dt)
        for i in enemies:
            if distance(self.pos, i.pos) < 20:
                dx = i.pos[0] - self.pos[0]
                dy = i.pos[1] - self.pos[1]
                dist = math.hypot(dx, dy)
                if dist != 0:
                    speed = math.hypot(*self.vel)
                    self.vel[0] = dx / dist * speed
                    self.vel[1] = dy / dist * speed
            if distance(self.pos, i.pos) < self.size + i.size:
                self.collided = True
                i.health -= 1
                break

camera = Camera((0,0), None)
player = Player([200,200], camera)
rift = Rift((0, 0), [], camera)

particles = []
stars = [Star((random.randint(0, W), random.randint(0, H)), random.random()+1, random.randint(1,5), (255,255,255), random.randint(1,3), camera) for i in range(100)]
enemies = []
bullets = []

camera.target = player
run = True
while run:
    dt = clock.tick(FPS)/1000

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    for i in stars:
        i.update(dt)

    for i in particles:
        i.update(dt)
        if i.time >= i.lifetime:
            particles.remove(i)

    rift.update(dt)

    for i in enemies:
        i.update(dt)
        bounce(i)
        if i.health <= 0:
            enemies.remove(i)
            i.on_death()

    for i in bullets:
        i.update(dt)
        bounce(i)
        if i.time >= i.lifetime or i.collided:
            bullets.remove(i)
    player.update(dt)
    bounce(player)

    camera.update(dt)


    screen.fill((10,10,50))
    pygame.draw.circle(screen, (0,0,0), (-camera.pos[0],-camera.pos[1]), 700)

    for i in stars:
        i.render(screen)

    for i in particles:
        i.render(screen)

    rift.render(screen)

    for i in bullets:
        i.render(screen)

    for i in enemies:
        i.render(screen)

    player.render(screen)
    player.render_UI(screen)

    pygame.display.update()
pygame.quit()
sys.exit()