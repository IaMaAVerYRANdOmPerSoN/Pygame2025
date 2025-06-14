import pygame
from pygame.locals import *
from enemy import RangedEnemy

class Game:
    def __init__(self, screen):
        self.screen = screen
        self.running = True
        self.player = None
        self.enemies = []
        self.enemy_health = 30
        self.enemy_spawn_rate = 3000
        self.enemy_speed = 1.0
        self.explosions = []

    def initialize(self):
        from player import Player
        self.player = Player()
        self.next_level_score = [10, 30, 50, 100] + [1.2**i + 40*i for i in range(5, 999)]  # Example score progression
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
            mouse_buttons = pygame.mouse.get_pressed()
            if mouse_buttons[0]:  # Left mouse button is held
                mouse_pos = pygame.mouse.get_pos()
                self.player.shoot(mouse_pos)
            # Handle bullet collisions with enemies
            for bullet in self.player.bullets[:]:  # Iterate over a copy!
                for enemy in self.enemies:
                    if enemy.rect.clipline(bullet.prev_pos, bullet.rect.center) or bullet.rect.colliderect(enemy.rect):
                        print("Collision detected!")
                        sound = pygame.mixer.Sound("hit.wav")
                        sound.set_volume(0.25)
                        sound.play()  # Play hit sound
                        if not hasattr(bullet, "already_hit"):
                            bullet.already_hit = set()
                        if enemy not in bullet.already_hit:
                            if hasattr(enemy, "take_damage"):
                                enemy.take_damage(getattr(bullet, "damage", 1))
                            if hasattr(bullet, "on_hit"):
                                bullet.on_hit(enemy)
                            bullet.already_hit.add(enemy)
                            bullet.pierced = getattr(bullet, "pierced", 0) + 1
                            if bullet.pierced > getattr(bullet, "pierce", 0):
                                if bullet in self.player.bullets:
                                    self.player.bullets.remove(bullet)
                            # Explosion logic
                            if getattr(bullet, "explosion_radius", 0) > 0:
                                for other_enemy in self.enemies:
                                    if other_enemy != enemy and other_enemy.rect.colliderect(
                                        bullet.rect.inflate(bullet.explosion_radius, bullet.explosion_radius)
                                    ):
                                        other_enemy.take_damage(getattr(bullet, "damage", 1))
                                    # Schedule explosion circle to be drawn for 0.5 seconds
                                    if not hasattr(self, "explosions"):
                                        self.explosions = []
                                    self.explosions.append({
                                        "pos": bullet.rect.center,
                                        "radius": bullet.explosion_radius,
                                        "start_time": pygame.time.get_ticks()
                                    })
                                sound = pygame.mixer.Sound("explosion.wav")
                                sound.set_volume(0.15)
                                sound.play()  # Play explosion sound
                            
                for explosion in getattr(self, "explosions", []):
                    if pygame.time.get_ticks() - explosion["start_time"] < 500:
                        pygame.draw.circle(self.screen, (255, 100, 0), explosion["pos"], explosion["radius"], 1)

            # Handle enemy bullet collisions with player
            for enemy in self.enemies:
                if isinstance(enemy, RangedEnemy) and hasattr(enemy, "bullets"):
                    for bullet in enemy.bullets[:]:
                        if bullet.rect.colliderect(self.player.rect):
                            print("Player hit by enemy bullet!")
                            self.player.health -= bullet.damage
                            enemy.bullets.remove(bullet)


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
                self.player.handle_upgrades(self.screen)
            
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                self.player.dash()
                


    def draw(self):
        self.screen.fill((0, 0, 0))
        self.player.draw(self.screen)
        for enemy in self.enemies:
            enemy.draw(self.screen)
            # Draw bullets for RangedEnemy
            if hasattr(enemy, "bullets"):
                for bullet in enemy.bullets:
                    bullet.draw(self.screen, (255, 0, 0))  # Draw enemy bullets in red
        # Draw explosions
        now = pygame.time.get_ticks()
        for explosion in getattr(self, "explosions", []):
            if now - explosion["start_time"] < 500:
                pygame.draw.circle(self.screen, (255, 100, 0), explosion["pos"], explosion["radius"])
        pygame.display.flip()
        # Clean up old explosions
        self.explosions = [e for e in self.explosions if now - e["start_time"] < 500]

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
        self.player.bullets = [b for b in self.player.bullets if 0 <= b.rect.x <= 1920 and 0 <= b.rect.y <= 1080]
        self.player.rect.topleft = self.player.position
        self.player.rect = pygame.Rect(self.player.position[0], self.player.position[1], *self.player.size)
        self.player.rect.clamp_ip(self.screen.get_rect())
        for enemy in self.enemies:
            enemy.update()
            # Call shoot for RangedEnemy
            if hasattr(enemy, "shoot"):
                enemy.shoot()

    def spawn_enemy(self):
        from enemy import Enemy, RangedEnemy
        import random
        x = random.randint(0, self.screen.get_width() - 50)
        y = random.randint(0, self.screen.get_height() - 50)
        kind = random.choice(["enemy", "ranged"])
        if kind == "enemy":
            enemy = Enemy(x, y, self.enemy_health, self.enemy_speed)
        elif kind == "ranged":
            enemy = RangedEnemy(x, y, self.enemy_health, self.enemy_speed, bullet_speed=3, bullet_damage=5)
        enemy.player = self.player
        self.enemies.append(enemy)