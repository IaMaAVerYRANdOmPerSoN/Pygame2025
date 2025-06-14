import pygame
import time
from player import Bullet  # Adjust import as needed

class Enemy:
    def __init__(self, x, y, health, speed):
        self.position = (x, y)
        self.health = health
        self.image = pygame.image.load("enemy.png")
        self.image = pygame.transform.scale(self.image, (80, 80))
        self.rect = self.image.get_rect(topleft=self.position)
        self.speed = speed
        
    def move(self, dx, dy):
        self.position = (self.position[0] + dx, self.position[1] + dy)
        self.rect.topleft = self.position

    def draw(self, screen):
        screen.blit(self.image, self.rect)

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            print("Enemy defeated!")

    def update(self):
        # Move towards the player
        if hasattr(self, 'player'):
            px, py = self.player.position
            ex, ey = self.position
            dx = px - ex
            dy = py - ey
            distance = (dx ** 2 + dy ** 2) ** 0.5
            angle = pygame.math.Vector2(dx, dy).angle_to((1, 0))
            self.image = pygame.transform.rotate(pygame.image.load("enemy.png"), angle + 90)
            self.image = pygame.transform.scale(self.image, (50, 50))
            self.rect = self.image.get_rect(center=self.rect.center)
            if distance != 0:
                move_x = self.speed * dx / distance
                move_y = self.speed * dy / distance
                self.move(move_x, move_y)

class RangedEnemy(Enemy):
    def __init__(self, x, y, health, speed, bullet_speed, bullet_damage):
        super().__init__(x, y, health, speed)
        self.bullet_speed = bullet_speed
        self.bullet_damage = bullet_damage
        self.bullet_cooldown = 2
        self.last_shot_time = 0
        self.bullets = []

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
                    damage=getattr(self, "bullet_damage", 10)
                )
                if not hasattr(self, "bullets"):
                    self.bullets = []
                self.bullets.append(bullet)
                self.last_shot_time = current_time
        
    def update(self):
        super().update()
        for bullet in self.bullets[:]:
            bullet.update()