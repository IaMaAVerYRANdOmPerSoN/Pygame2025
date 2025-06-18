import pygame
import time
from player import Bullet  # Adjust import as needed
from pickup import Pickup
import random
from numpy import sign
import math

ENEMY_IMAGE = pygame.image.load("enemy_1.png")
ENEMY_IMAGE = pygame.transform.scale(ENEMY_IMAGE, (80, 80))

RANGED_ENEMY_IMAGE = pygame.image.load("enemy_2.png")
RANGED_ENEMY_IMAGE = pygame.transform.scale(RANGED_ENEMY_IMAGE, (80, 80))

SPAWNER_ENEMY_IMAGE = pygame.image.load("enemy_3.png")
SPAWNER_ENEMY_IMAGE = pygame.transform.scale(SPAWNER_ENEMY_IMAGE, (80, 80))

MISSLE_IMAGE = pygame.image.load("Enemy_Missile.png")

enemies_killed_melee = 0
enemies_killed_ranged = 0
enemies_killed_spawner = 0

class Enemy:
    def __init__(self, x, y, health, speed, chance):
        self.position = (x, y)
        self.image = ENEMY_IMAGE.copy()
        self.health = health
        self.rect = self.image.get_rect(topleft=self.position)
        self.speed = speed
        self.pickup_chance = chance
        
        
    def move(self, dx, dy):
        # Clamp position to keep enemy within screen bounds
        new_x = self.position[0] + dx
        new_y = self.position[1] + dy
        width, height = self.rect.size
        screen_width, screen_height = 1920, 1080
        clamped_x = max(0, min(new_x, screen_width - width))
        clamped_y = max(0, min(new_y, screen_height - height))
        self.position = (clamped_x, clamped_y)
        self.rect.topleft = self.position

    def draw(self, screen):
        screen.blit(self.image, self.rect)

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            print("Enemy defeated!")
            global enemies_killed_melee, enemies_killed_ranged, enemies_killed_spawner
            if isinstance(self, RangedEnemy):
                enemies_killed_ranged += 1
            elif isinstance(self, SpawnerEnemy):
                enemies_killed_spawner += 1
            else:
                enemies_killed_melee += 1

    def DropPickup(self):
        if random.random() < self.pickup_chance:  # 10% chance to drop a pickup
            pickup_type = random.choice(["health", "damage", "speed", "health", "damage", "speed", "overload"])
            if pickup_type == "health":
                image = pygame.image.load("health_pickup.png").convert_alpha()
            elif pickup_type == "damage":
                image = pygame.image.load("damage_pickup.png").convert_alpha()
            elif pickup_type == "speed":
                image = pygame.image.load("speed_pickup.png").convert_alpha()
            elif pickup_type == "overload":
                image = pygame.image.load("overload_pickup.png").convert_alpha()
            else:
                image = None
            return Pickup(self.rect.centerx, self.rect.centery, size=(50, 50), image=image, kind=pickup_type)
        
        

    def update(self):
        # Move towards the player
        if hasattr(self, 'player'):
            px, py = self.player.position
            ex, ey = self.position
            dx = px - ex
            dy = py - ey
            distance = (dx ** 2 + dy ** 2) ** 0.5
            angle = pygame.math.Vector2(dx, dy).angle_to((1, 0))
            self.image = pygame.transform.rotate(pygame.image.load("enemy_1.png"), angle - 90)
            self.image = pygame.transform.scale(self.image, (50, 50))
            self.rect = self.image.get_rect(center=self.rect.center)
            if distance != 0:
                move_x = self.speed * dx / distance
                move_y = self.speed * dy / distance
                self.move(move_x, move_y)

class RangedEnemy(Enemy):
    def __init__(self, x, y, health, speed, bullet_speed, bullet_damage, chance):
        self.bullet_speed = bullet_speed
        self.bullet_damage = bullet_damage
        self.bullet_cooldown = 2
        self.last_shot_time = 0
        self.bullets = []
        self.bullet_image = pygame.image.load("Enemy_Bullet.png")
        super().__init__(x, y, health, speed, chance)
        self.image = RANGED_ENEMY_IMAGE.copy()
        

    def shoot(self):
        current_time = time.time()
        if current_time - self.last_shot_time >= self.bullet_cooldown:
            if hasattr(self, 'player'):
                # Get the center of the enemy
                ex, ey = self.rect.center
                # Get the center of the player
                px = self.player.position[0] + self.player.size[0] // 2
                py = self.player.position[1] + self.player.size[1] // 2
                # Create the bullet
                bullet = Bullet(
                    ex, ey,
                    px, py,
                    size=getattr(self, "bullet_size", 20),
                    speed=getattr(self, "bullet_speed", 2),
                    damage=getattr(self, "bullet_damage", 10),
                    image = getattr(self, "bullet_image", None)
                )
                if not hasattr(self, "bullets"):
                    self.bullets = []
                self.bullets.append(bullet)
                self.last_shot_time = current_time
        
    def update(self):
        if hasattr(self, 'player'):
            px, py = self.player.position
            ex, ey = self.position
            dx = px - ex
            dy = py - ey
            distance = (dx ** 2 + dy ** 2) ** 0.5
            angle = pygame.math.Vector2(dx, dy).angle_to((1, 0))
            self.image = pygame.transform.rotate(RANGED_ENEMY_IMAGE, angle + 90)
            self.image = pygame.transform.scale(self.image, (50, 50))
            self.rect = self.image.get_rect(center=self.rect.center)
            if distance != 0:
                move_x = self.speed * dx / distance
                move_y = self.speed * dy / distance
            self.move(move_x, move_y)
        for bullet in self.bullets[:]:
            bullet.update()

class SpawnerEnemy(Enemy):
    def __init__(self, x, y, health, speed, game=None, chance=None):
        super().__init__(x, y, health, speed, chance)
        self.spawn_rate = 5
        self.image = SPAWNER_ENEMY_IMAGE.copy()
        self.rect = self.image.get_rect(topleft=(x, y))
        self.last_spawn_time = 0
        self.game = game

    def spawn_enemy(self):
        current_time = time.time()
        if current_time - self.last_spawn_time >= self.spawn_rate:
            new_enemy = Enemy(self.rect.centerx, self.rect.centery, self.health / 3, self.speed, self.game.pickup_chance)
            new_enemy.rect = new_enemy.image.get_rect(center=self.rect.center)
            new_enemy.player = self.player  # Ensure the new enemy has a reference to the player
            if self.game:  # Use self.game, not global game
                self.game.enemies.append(new_enemy)
                screen_rect = self.game.screen.get_rect()
                new_enemy.rect.clamp_ip(screen_rect)
            self.last_spawn_time = current_time

    def update(self):
        if hasattr(self, 'player'):
            px, py = self.player.position
            ex, ey = self.position
            dx = px - ex
            dy = py - ey
            distance = (dx ** 2 + dy ** 2) ** 0.5
            angle = pygame.math.Vector2(dx, dy).angle_to((1, 0))
            self.image = pygame.transform.rotate(SPAWNER_ENEMY_IMAGE, angle + 90)
            self.image = pygame.transform.scale(self.image, (80, 80))
            self.rect = self.image.get_rect(center=self.rect.center)
            if distance != 0:
                move_x = -self.speed * dx / distance
                move_y = -self.speed * dy / distance
                self.move(move_x, move_y)
        self.spawn_enemy()

class Missle():
    def __init__(self, distance, angle, x, y, speed = 6, radius = 80, damage = 20):
        self.distance = distance
        self.angle = angle
        self.x, self.y = (x, y)
        self.speed = speed
        self.original_image = pygame.transform.scale(MISSLE_IMAGE.copy(), (30, 30)) # Store the original image
        self.image = self.original_image.copy()
        self.radius = radius
        self.damage = damage
        self.rect = self.image.get_rect(center=(self.x, self.y))

    def move(self, distance, angle):
        radians = math.radians(angle)
        self.x += distance * math.cos(radians)
        self.y += distance * math.sin(radians)

    def update(self, target_x, target_y):
        dx = target_x - self.x
        dy = target_y - self.y
        self.distance = (dx ** 2 + dy ** 2) ** 0.5
        target_angle = -pygame.math.Vector2(dx, dy).angle_to((1, 0))
        max_turn = 1/2
        angle_diff = (target_angle - self.angle + 180) % 360 - 180
        if abs(angle_diff) > max_turn:
            self.angle += max_turn * sign(angle_diff)
        else:
            self.angle = target_angle

        self.image = pygame.transform.rotate(self.original_image, -self.angle - 90)
        self.rect = self.image.get_rect(center=(self.x, self.y))
        self.move(self.speed, self.angle)
    
    def draw(self, screen):
        screen.blit(self.image, self.rect)
        pygame.draw.rect(screen, (255,0,0), self.rect, 2)


class BossEnemy(SpawnerEnemy):
    def __init__(self):
        super().__init__(x = 0, y = 0, health = 100000, speed = 0.5, chance = 1, game = None)
        self.x, self.y = self.position
        self.spawn_rate = 1.5
        self.missle_spawn_rate = 1.5
        self.base_image = pygame.transform.scale(SPAWNER_ENEMY_IMAGE.copy(), (250, 250))
        self.image = self.base_image.copy()
        self.rect = self.image.get_rect(topleft=(self.x, self.y))
        self.last_spawn_time = 0
        self.last_missle_time = 0
        self.missles = []
    
    def spawn_missle(self):
        now = time.time() 
        if hasattr(self, 'player') and (now - self.last_missle_time >= self.spawn_rate):
            self.last_missle_time = now
            px, py = self.player.position
            ex, ey = self.position
            dx = px - ex
            dy = py - ey
            distance = (dx ** 2 + dy ** 2) ** 0.5
            angle = -pygame.math.Vector2(dx, dy).angle_to((1, 0))
            self.missles.append(Missle(distance, angle, ex, ey))

    def update(self):
        super(type(self).__bases__[0], self).update()
        if hasattr(self, 'player'):
            px, py = self.player.position
            ex, ey = self.position
            dx = px - ex
            dy = py - ey
            angle = pygame.math.Vector2(dx, dy).angle_to((1, 0))
            self.image = pygame.transform.rotate(self.base_image, angle + 90)
            self.rect = self.image.get_rect(center=self.rect.center)
        self.spawn_missle()
        self.spawn_enemy()

    def spawn_enemy(self):
        current_time = time.time()
        if current_time - self.last_spawn_time >= self.spawn_rate:
            new_enemy = Enemy(self.rect.centerx, self.rect.centery, self.health / 100, self.speed * 4, self.game.pickup_chance)
            new_enemy.rect = new_enemy.image.get_rect(center=self.rect.center)
            new_enemy.player = self.player
            if self.game:
                self.game.enemies.append(new_enemy)
                screen_rect = self.game.screen.get_rect()
                new_enemy.rect.clamp_ip(screen_rect)
            self.last_spawn_time = current_time
        
