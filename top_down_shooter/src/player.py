import pygame
from pygame.locals import *
import math
import time

class Bullet:
    def __init__(self, x, y, target_x, target_y, size = 10, speed = 10, damage = 10, count = 1, prierce = 0, explosion_radius = 0):
        self.size = size
        self.rect = pygame.Rect(x + 20, y + 20, self.size, self.size)
        self.speed = speed
        dx = target_x - (x + 25)
        dy = target_y - (y + 25)
        distance = math.hypot(dx, dy)
        if distance == 0:
            distance = 1
        self.velocity = (dx / distance * self.speed, dy / distance * self.speed)
        self.damage = damage

    def update(self):
        self.rect.x += self.velocity[0]
        self.rect.y += self.velocity[1]

    def draw(self, screen):
        pygame.draw.rect(screen, (255, 255, 0), self.rect)

class Player:
    def __init__(self):
        self.position = [400, 300]
        self.speed = 5
        self.size = (50, 50)
        self.color = (255, 0, 0)
        self.rect = pygame.Rect(self.position[0], self.position[1], *self.size)
        self.health = 100
        self.score = 0
        self.bullet_count = 0
        self.bullet_speed = 15
        self.bullet_damage = 10
        self.bullet_cooldown = 0.5  # seconds
        self.health_regen = 2
        self.last_shot_time = 0
        self.bullets = []
        self.upgrade_options = {
            "Increase bullet speed": 0.15,
            "Increase bullet damage": 0.15,
            "Increase health": 0.15,
            "Increase firerate": 0.15,
            "Increase player speed": 0.15,
            "Increase bullet size": 0.15,
            "Increase Health regeneration": 0.05,
            "Increase bullet count": 0.02,
            "Increase bullet piercing": 0.02,
            "Increase bullet explosion radius" : 0.01
        } # Upgrade : Chance

    def move(self, dx, dy):
        self.position[0] += dx
        self.position[1] += dy

    def shoot(self, target_pos):
        current_time = time.time()
        if current_time - self.last_shot_time >= self.bullet_cooldown:
            bullet = Bullet(self.position[0], self.position[1], target_pos[0], target_pos[1], bullet_speed=self.bullet_speed, damage=self.bullet_damage, count=self.bullet_count)
            self.bullets.append(bullet)
            self.last_shot_time = current_time
            print(f"Bullet fired! Total bullets: {len(self.bullets)}")

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        for bullet in self.bullets:
            bullet.draw(screen)
        # Draw health bar
        health_bar_length = 100
        health_bar_height = 10
        health_ratio = self.health / 100
        pygame.draw.rect(screen, (255, 0, 0), (self.position[0], self.position[1] - 20, health_bar_length, health_bar_height))
        pygame.draw.rect(screen, (0, 255, 0), (self.position[0], self.position[1] - 20, health_bar_length * health_ratio, health_bar_height))

    def Handle_upgrades(self):
        Upgrade = random.randint(0, 100)
        cumulative = 0
        rand_val = Upgrade / 100  # Convert to 0-1 range
        for upgrade, chance in self.upgrade_options.items():
            cumulative += chance
            if rand_val <= cumulative:
                if upgrade == "Increase bullet speed":
                    self.bullet_speed += 2
                elif upgrade == "Increase bullet damage":
                    self.bullet_damage += 5
                elif upgrade == "Increase health":
                    self.health += 20
                elif upgrade == "Increase firerate":
                    self.bullet_cooldown = self.bullet_cooldown - 0.05
                elif upgrade == "Increase player speed":
                    self.speed += 1
                elif upgrade == "Increase bullet size":
                    self.size = (self.size[0] + 2, self.size[1] + 2)
                    pass
                elif upgrade == "Increase Health regeneration":
                    self.health_regen += 1
                elif upgrade == "Increase bullet count":
                    self.bullet_count += 1
                elif upgrade == "Increase bullet piercing":
                    # You may want to add a bullet_piercing attribute
                    pass
                elif upgrade == "Increase bullet explosion radius":
                    # You may want to add a bullet_explosion_radius attribute
                    pass
                print(f"Upgrade applied: {upgrade}")
                break
