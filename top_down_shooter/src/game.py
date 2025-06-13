import pygame
from pygame.locals import *

class Game:
    def __init__(self, screen):
        self.screen = screen
        self.running = True
        self.player = None
        self.enemies = []

    def initialize(self):
        from player import Player
        self.player = Player()
        self.next_level_score = [10, 30, 50, 100] + [1.1**i + 50*i for i in range(5, 999)]  # Example score progression
        self.level = 0

    def handle_events(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            self.player.move(0, -self.player.speed)
        if keys[pygame.K_s]:
            self.player.move(0, self.player.speed)
        if keys[pygame.K_a]:
            self.player.move(-self.player.speed, 0)
        if keys[pygame.K_d]:
            self.player.move(self.player.speed, 0)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                self.player.shoot(mouse_pos)
            # Handle bullet collisions with enemies
            for bullet in self.player.bullets[:]:
                for enemy in getattr(self, "enemies", []):
                    if bullet.rect.colliderect(enemy.rect):
                        if hasattr(enemy, "take_damage"):
                            enemy.take_damage(bullet.damage if hasattr(bullet, "damage") else 1)
                        if hasattr(bullet, "on_hit"):
                            bullet.on_hit(enemy)
                        if getattr(bullet, "destroy_on_hit", True):
                            self.player.bullets.remove(bullet)
                        break

            for enemy in getattr(self, "enemies", []):
                if hasattr(enemy, "update"):
                    enemy.update()
                if hasattr(enemy, "rect") and enemy.rect.colliderect(self.player.rect):
                    self.player.health -= 12
                    enemy.take_damage(enemy.health)  # kill the enemy on collision
                    if self.player.health <= 0:
                        print("Player defeated!")
                        print(f"Final Score: {self.player.score}")
                        self.running = False
                if enemy.health <= 0:
                    self.enemies.remove(enemy)
                    self.player.score += 10
                    print(f"Enemy defeated! Score: {self.player.score}")

            if self.player.score >= self.next_level_score[self.level]:
                self.level += 1
                print(f"Level up! Now at level {self.level}")
                font = pygame.font.SysFont(None, 48)
                upgrade_text = font.render("Pick an upgrade!", True, (255, 255, 0))
                text_rect = upgrade_text.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2 * 1.8))
                self.screen.blit(upgrade_text, text_rect)
                pygame.display.flip()
                roll
                


    def draw(self):
        self.screen.fill((0, 0, 0))
        self.player.draw(self.screen)
        for enemy in self.enemies:
            enemy.draw(self.screen) 
        pygame.display.flip()

    def run(self):
        self.initialize()
        while self.running:
            self.handle_events()
            self.update()
            self.draw()

    def update(self):
        for bullet in self.player.bullets:
            bullet.update()
        # Remove bullets that go off screen
        self.player.bullets = [b for b in self.player.bullets if 0 <= b.rect.x <= 800 and 0 <= b.rect.y <= 600]
        self.player.rect.topleft = self.player.position
        self.player.rect = pygame.Rect(self.player.position[0], self.player.position[1], *self.player.size)
        self.player.rect.clamp_ip(self.screen.get_rect())
        for enemy in self.enemies:
            enemy.update()

    def spawn_enemy(self):
        from enemy import Enemy
        import random
        x = random.randint(0, self.screen.get_width() - 50)
        y = random.randint(0, self.screen.get_height() - 50)
        health = 30
        enemy = Enemy(x, y, health)
        enemy.player = self.player
        self.enemies.append(enemy)