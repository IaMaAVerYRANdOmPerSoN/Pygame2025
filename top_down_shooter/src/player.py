import pygame
from pygame.locals import *
import math
import time
import random

class Bullet:
    def __init__(self, x, y, target_x, target_y, size=10, speed=10, damage=10, count=1, pierce=0, explosion_radius=0, image = None):
        self.size = size
        self.rect = pygame.Rect(x + 20, y + 20, self.size, self.size)
        self.speed = speed
        self.prev_pos = self.rect.center
        dx = target_x - (x + 25)
        dy = target_y - (y + 25)
        distance = math.hypot(dx, dy)
        if distance == 0:
            distance = 1
        self.velocity = (dx / distance * self.speed, dy / distance * self.speed)
        self.damage = damage
        self.count = count
        self.pierce = pierce
        self.explosion_radius = explosion_radius
        self.pierced = 0  # Track how many enemies pierced
        # Load bullet image and scale to bullet size
        self.image = image
        self.image = pygame.transform.scale(self.image, (self.size, self.size))
    def update(self):
        self.prev_pos = self.rect.center
        self.rect.x += self.velocity[0]
        self.rect.y += self.velocity[1]

    def draw(self, screen, color=(255, 255, 0)):
        # Draw the bullet image if available, else fallback to rect
        if hasattr(self, "image") and self.image:
            screen.blit(self.image, self.rect)
        else:
            pygame.draw.rect(screen, color, self.rect)

class Player:
    def __init__(self):
        self.position = [400, 300]
        self.speed = 5
        self.size = (104, 88)
        self.image = pygame.image.load("player.png")
        self.color = (255, 0, 0)
        self.rect = pygame.Rect(
            self.position[0] - self.size[0] // 2,
            self.position[1] - self.size[1] // 2,
            *self.size
        )
        self.health = 100
        self.max_health = 100
        self.score = 0
        self.bullet_count = 1
        self.bullet_speed = 15
        self.bullet_damage = 10
        self.bullet_size = 10
        self.bullet_cooldown = 0.5  # seconds
        self.health_regen = 5
        self.bullet_piercing = 0
        self.bullet_explosion_radius = 0
        self.last_shot_time = 0
        self.bullets = []
        self.upgrade_options = {
            f"Increase bullet speed ({self.bullet_speed} > {self.bullet_speed + 2})": 0.15,
            f"Increase bullet damage ({self.bullet_damage} > {self.bullet_damage + 2})": 0.15,
            f"Increase health ({self.max_health} > {self.max_health + 20})": 0.15,
            f"Increase firerate ({self.bullet_cooldown:.2f}s > {max(0.1, self.bullet_cooldown - 0.05):.2f}s)": 0.15,
            f"Increase player speed ({self.speed} > {self.speed + 1})": 0.15,
            f"Increase bullet size ({self.bullet_size} > {self.bullet_size + 2})": 0.15,
            f"Increase Health regeneration ({self.health_regen} > {self.health_regen + 1})": 0.05,
            f"Increase bullet count ({self.bullet_count} > {self.bullet_count + 1})": 0.02,
            f"Increase bullet piercing ({self.bullet_piercing} > {self.bullet_piercing + 1})": 0.02,
            f"Increase bullet explosion radius ({self.bullet_explosion_radius} > {self.bullet_explosion_radius + 10})": 0.01
        }  # Upgrade : Chance
        self.UPGRADE_COLORS = [(200, 200, 0), (0, 200, 200), (200, 0, 200)]
        self.dash_cooldown = 10  # seconds
        self.dash_distance = 500
        self.dash_speed = self.speed * 3
        self.last_dash_time = 0
        self.bullet_image = pygame.image.load("Player_Bullet.png")
        self.next_level_score = [10, 30, 50, 100] + [1.2**i + 40*i for i in range(5, 999)]  # Example score progression
        self.level = 0  # Player level
        
    def move(self, dx, dy):
        self.position[0] += dx if 0 <= self.position[0] + dx <= 1920 - self.size[0] else 0
        self.position[1] += dy if 0 <= self.position[1] + dy <= 1080 - self.size[1] else 0

    def shoot(self, target_pos):
        current_time = time.time()
        if current_time - self.last_shot_time >= self.bullet_cooldown:
            # Calculate the center of the player sprite
            player_center_x = self.position[0] + self.size[0] // 2
            player_center_y = self.position[1] + self.size[1] // 2

            angle_to_mouse = math.atan2(
                target_pos[1] - player_center_y,
                target_pos[0] - player_center_x
            )
            spread = 0.15  # radians, adjust for wider/narrower spread
            count = self.bullet_count

            for i in range(count):
                if count > 1:
                    angle = angle_to_mouse + spread * (i - (count - 1) / 2)
                    dx = math.cos(angle)
                    dy = math.sin(angle)
                    tx = player_center_x + dx * 100
                    ty = player_center_y + dy * 100
                else:
                    tx, ty = target_pos
                bullet = Bullet(
                    player_center_x, player_center_y,
                    tx, ty,
                    size=self.bullet_size,
                    speed=self.bullet_speed,
                    damage=self.bullet_damage,
                    count=self.bullet_count,
                    pierce=self.bullet_piercing,
                    explosion_radius=self.bullet_explosion_radius,
                    image = self.bullet_image
                )
                self.bullets.append(bullet)
            self.last_shot_time = current_time
            print(f"Bullet fired! Total bullets: {len(self.bullets)}")
            sound = pygame.mixer.Sound("shoot.mp3")
            sound.set_volume(0.25)
            sound.play()  # Play shooting sound

    def draw(self, screen):
        # Calculate the center of the player
        player_center = (self.position[0] + self.size[0] // 2, self.position[1] + self.size[1] // 2)
        mouse_x, mouse_y = pygame.mouse.get_pos()
        dx = mouse_x - player_center[0]
        dy = mouse_y - player_center[1]
        angle = math.degrees(math.atan2(-dy, dx))  # Negative dy because pygame's y-axis is down

        # Rotate the image
        rotated_image = pygame.transform.rotate(self.image, angle + -90)
        rotated_rect = rotated_image.get_rect(center=player_center)

        # Draw the rotated image
        screen.blit(rotated_image, rotated_rect.topleft)

        # Draw bullets
        for bullet in self.bullets:
            bullet.draw(screen)
        # Draw health bar
        health_bar_length = 100
        health_bar_height = 10
        health_ratio = self.health / 100
        pygame.draw.rect(screen, (255, 0, 0), (self.position[0], self.position[1] - 20, health_bar_length, health_bar_height))
        pygame.draw.rect(screen, (0, 255, 0), (self.position[0], self.position[1] - 20, health_bar_length * health_ratio, health_bar_height))

        dash_bar_length = 100
        dash_bar_height = 10
        dash_ratio = (time.time() - self.last_dash_time) / self.dash_cooldown
        pygame.draw.rect(screen, (255, 255, 0), (self.position[0], self.position[1] - 40, dash_bar_length, dash_bar_height))
        fill_width = dash_bar_length * (1 - dash_ratio)
        fill_x = self.position[0] + (dash_bar_length - fill_width)
        pygame.draw.rect(screen, (255,0 , 255), (fill_x, self.position[1] - 40, fill_width, dash_bar_height))

        # Progress bar for next level
        Next_level_bar_length = screen.get_width() - 200
        Next_level_bar_height = 30
        if self.level == 0:
            prev_score = 0
        else:
            prev_score = self.next_level_score[self.level - 1]
        next_score = self.next_level_score[self.level]
        Next_level_ratio = (self.score - prev_score) / (next_score - prev_score)
        Next_level_ratio = max(0, min(Next_level_ratio, 1))  # Clamp between 0 and 1

        pygame.draw.rect(screen, (50, 50, 50), (100, screen.get_height() - 50, Next_level_bar_length, Next_level_bar_height))
        pygame.draw.rect(screen, (70, 130, 255), (100, screen.get_height() - 50, Next_level_bar_length * Next_level_ratio, Next_level_bar_height))
        # Draw score
        font = pygame.font.SysFont(None, 36)
        score_text = font.render(f"Score: {self.score}", True, (255, 255, 255))
        screen.blit(score_text, (10, 10))




    def apply_upgrade(self, upgrade_name):
        upgrade_options = self.get_upgrade_options()
        upgrade = upgrade_options[upgrade_name]
        if upgrade == "bullet_speed":
            self.bullet_speed += 2
        elif upgrade == "bullet_damage":
            self.bullet_damage += 2
        elif upgrade == "health":
            self.health += 20
        elif upgrade == "bullet_cooldown":
            self.bullet_cooldown = max(0.1, self.bullet_cooldown - 0.05)
        elif upgrade == "speed":
            self.speed += 1
        elif upgrade == "bullet_size":
            self.bullet_size += 2
        elif upgrade == "health_regen":
            self.health_regen += 1
        elif upgrade == "bullet_count":
            self.bullet_count += 1
        elif upgrade == "bullet_piercing":
            self.bullet_piercing += 1
        elif upgrade == "bullet_explosion_radius":
            self.bullet_explosion_radius += 10
        elif upgrade == "dash_cooldown":
            self.dash_cooldown = max(1, self.dash_cooldown - 1)

    def get_upgrade_options(self):
        return {
            f"Increase bullet speed ({self.bullet_speed} > {self.bullet_speed + 2})": "bullet_speed",
            f"Increase bullet damage ({self.bullet_damage} > {self.bullet_damage + 2})": "bullet_damage",
            f"Increase health ({self.health} > {self.health + 20})": "health",
            f"Increase firerate ({self.bullet_cooldown:.2f}s > {max(0.1, self.bullet_cooldown - 0.05):.2f}s)": "bullet_cooldown",
            f"Increase player speed ({self.speed} > {self.speed + 1})": "speed",
            f"Increase bullet size ({self.bullet_size} > {self.bullet_size + 2})": "bullet_size",
            f"Increase Health regeneration ({self.health_regen} > {self.health_regen + 1})": "health_regen",
            f"Increase bullet count ({self.bullet_count} > {self.bullet_count + 1})": "bullet_count",
            f"Increase bullet piercing ({self.bullet_piercing} > {self.bullet_piercing + 1})": "bullet_piercing",
            f"Increase bullet explosion radius ({self.bullet_explosion_radius} > {self.bullet_explosion_radius + 10})": "bullet_explosion_radius",
            f"Decrease dash cooldown ({self.dash_cooldown} > {max(1, self.dash_cooldown - 1)})": "dash_cooldown"
        }

    def handle_upgrades(self, screen):
        font = pygame.font.SysFont(None, 36)
        # Pick 3 random upgrades
        upgrade_options = self.get_upgrade_options()
        options = random.sample(list(upgrade_options.keys()), 3)
        buttons = []
        button_rects = []
        width, height = 1080, 60  # Increased width for longer buttons
        spacing = 40
        start_y = screen.get_height() // 2 - (height + spacing)  # Center the buttons

        for i, option in enumerate(options):
            rect = pygame.Rect(
                screen.get_width() // 2 - width // 2,
                start_y + i * (height + spacing),
                width, height
            )
            button_rects.append(rect)
            buttons.append(option)

        # Draw buttons
        for i, rect in enumerate(button_rects):
            pygame.draw.rect(screen, self.UPGRADE_COLORS[i % len(self.UPGRADE_COLORS)], rect)
            text = font.render(buttons[i], True, (0, 0, 0))
            text_rect = text.get_rect(center=rect.center)
            screen.blit(text, text_rect)
        pygame.display.flip()

        # Wait for user to click a button
        picked = False
        while not picked:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_pos = pygame.mouse.get_pos()
                    for i, rect in enumerate(button_rects):
                        if rect.collidepoint(mouse_pos):
                            self.apply_upgrade(buttons[i])
                            picked = True
                            break



    def dash(self):
        current_time = time.time()
        if current_time - self.last_dash_time >= self.dash_cooldown:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            player_center_x = self.position[0] + self.size[0] // 2
            player_center_y = self.position[1] + self.size[1] // 2
            dx = mouse_x - player_center_x
            dy = mouse_y - player_center_y
            distance = math.hypot(dx, dy)
            if distance == 0:
                distance = 1
            dx /= distance
            dy /= distance
            new_x = self.position[0] + dx * self.dash_distance
            new_y = self.position[1] + dy * self.dash_distance
            self.position[0] = max(0, min(new_x, 1920 - self.size[0]))
            self.position[1] = max(0, min(new_y, 1080 - self.size[1]))
            self.last_dash_time = current_time
            print("Dashing!")