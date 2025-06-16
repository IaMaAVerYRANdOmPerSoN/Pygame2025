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

class Mine:
    def __init__(self, x, y, size=50, damage=50, explosion_radius=100, image=None):
        self.position = pygame.Vector2(x, y)
        self.size = size
        self.damage = damage
        self.explosion_radius = explosion_radius
        self.image = image if image else pygame.Surface((size, size))
        self.rect = self.image.get_rect(topleft=(x, y))

    def draw(self, surface):
        surface.blit(self.image, self.rect.topleft)

    def update(self):
        self.rect.topleft = (self.position.x, self.position.y)

import pygame
import time

import pygame
import time

class EnergyBlast:
    def __init__(self, player, draw_callback=None):
        self.player = player
        self.active = False
        self.start_time = 0
        self.duration = 0.5  # seconds
        self.radius = 500
        self.current_radius = 0
        self.max_radius = 500
        self.damage = 120
        self.knockback = 100
        self.cooldown = 5
        self.last_used = 0
        self.sound = pygame.mixer.Sound("energy_blast.mp3")
        self.sound.set_volume(0.25)
        self.draw_callback = draw_callback
        self.enemies_hit = set()

    def start(self, cooldown=5, radius=500, damage=120, knockback=200):
        now = time.time()
        if now - self.last_used >= cooldown and not self.active:
            self.active = True
            self.start_time = now
            self.duration = 0.5  # seconds for the animation
            self.radius = radius
            self.max_radius = radius
            self.current_radius = 0
            self.damage = damage
            self.knockback = knockback
            self.last_used = now
            self.enemies_hit = set()
            self.sound.stop()  # Stop any currently playing instance
            self.sound.play()  # Play the energy blast sound, overwriting others

    def update(self, enemies):
        if not self.active:
            return
        elapsed = time.time() - self.start_time
        progress = min(1.0, elapsed / self.duration)
        self.current_radius = int(self.max_radius * progress)
        # Apply effects when the animated circle intersects the enemy rect
        blast_center = (
            self.player.position[0] + self.player.size[0] // 2,
            self.player.position[1] + self.player.size[1] // 2
        )
        for enemy in enemies:
            if enemy in self.enemies_hit:
                continue
            # Check if the current animated circle intersects the enemy's rect
            enemy_center = enemy.rect.center
            dist = ((enemy_center[0] - blast_center[0]) ** 2 + (enemy_center[1] - blast_center[1]) ** 2) ** 0.5
            # Use current_radius for intersection
            if dist <= self.current_radius:
                if hasattr(enemy, "take_damage"):
                    enemy.take_damage(self.damage)
                dx = enemy_center[0] - blast_center[0]
                dy = enemy_center[1] - blast_center[1]
                if dx != 0 or dy != 0:
                    norm = (dx ** 2 + dy ** 2) ** 0.5
                    knockback_x = self.knockback * dx / norm if norm else 0
                    knockback_y = self.knockback * dy / norm if norm else 0
                    if hasattr(enemy, "move"):
                        enemy.move(knockback_x, knockback_y)
                self.enemies_hit.add(enemy)
        if progress >= 1.0:
            self.active = False

    def draw(self, surface):
        if not self.active:
            return
        blast_center = (
            self.player.position[0] + self.player.size[0] // 2,
            self.player.position[1] + self.player.size[1] // 2
        )
        pygame.draw.circle(surface, (70, 130, 255), blast_center, self.current_radius, 5)

class Player:
    def __init__(self):
        self.game = None
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
        self.orginal_bullet_cooldown = self.bullet_cooldown  # Store original cooldown for upgrades
        self.health_regen = 5
        self.bullet_piercing = 0
        self.bullet_explosion_radius = 0
        self.last_shot_time = 0
        self.last_mine_drop_time = 0
        self.last_mine_drop_cooldown = 2.5
        self.mine_damage = 200
        self.mine_explosion_radius = 300
        self.mine_image = pygame.image.load("mine.png")
        self.bullets = []
        self.base_bullet_cooldown = 0.5  # Store base value
        self.base_bullet_speed = 15
        self.base_bullet_damage = 10
        self.base_speed = 5
        self.base_bullet_size = 10
        self.base_health_regen = 5
        self.UPGRADE_COLORS = [(200, 200, 0), (0, 200, 200), (200, 0, 200)]
        self.dash_cooldown = 10  # seconds
        self.dash_distance = 500
        self.dash_speed = self.speed * 3
        self.last_dash_time = 0
        self.bullet_image = pygame.image.load("Player_Bullet.png")
        self.next_level_score = [10, 30, 50, 100] + [1.2**i + 50*i for i in range(5, 999)]  # Example score progression
        self.level = 0  # Player level
        self.mines = []  # List to hold mines
        self.energy_blast_cooldown = 5  # seconds
        self.energy_blast_radius = 500  # Radius of the energy blast
        self.energy_blast_damage = 120  # Damage of the energy blast
        self.energy_blast_knockback = 80  # Knockback distance for enemies hit by the blast
        self.energy_blast = EnergyBlast(self, draw_callback=None)  # Initialize energy blast with player reference
        
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

    def drop_mine(self):
        current_time = time.time()
        if current_time - self.last_mine_drop_time >= self.last_mine_drop_cooldown:
            # Drop mine at a random position on the screen
            screen_width, screen_height = 1920, 1080
            mine_x = random.randint(0, screen_width - 50)
            mine_y = random.randint(0, screen_height - 50)
            mine = Mine(
                mine_x,
                mine_y,
                size=50,
                damage=self.mine_damage,
                explosion_radius=self.mine_explosion_radius,
                image=self.mine_image
            )
            self.mines.append(mine)
            self.last_mine_drop_time = current_time

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
            self.base_bullet_speed += 2
            self.bullet_speed = self.base_bullet_speed
        elif upgrade == "bullet_damage":
            self.base_bullet_damage += 2
            self.bullet_damage = self.base_bullet_damage
        elif upgrade == "bullet_cooldown":
            self.base_bullet_cooldown = max(0.1, self.base_bullet_cooldown - 0.05)
            self.bullet_cooldown = self.base_bullet_cooldown
        elif upgrade == "speed":
            self.base_speed += 1
            self.speed = self.base_speed
        elif upgrade == "bullet_size":
            self.base_bullet_size += 2
            self.bullet_size = self.base_bullet_size
        elif upgrade == "health_regen":
            self.base_health_regen += 1
            self.health_regen = self.base_health_regen
        elif upgrade == "bullet_count":
            self.bullet_count += 1
        elif upgrade == "bullet_piercing":
            self.bullet_piercing += 1
        elif upgrade == "bullet_explosion_radius":
            self.bullet_explosion_radius += 10
        elif upgrade == "dash_cooldown":
            self.dash_cooldown = max(1, self.dash_cooldown - 1)
        elif upgrade == "mine_damage":
            self.mine_damage += 10
        elif upgrade == "mine_explosion_radius":
            self.mine_explosion_radius += 20
        elif upgrade == "mine_cooldown":
            self.last_mine_drop_cooldown = max(0.1, self.last_mine_drop_cooldown - 0.5)
        elif upgrade == "energy_blast_damage":
            self.energy_blast_damage += 30
        elif upgrade == "energy_blast_radius":
            self.energy_blast_radius += 50
        elif upgrade == "energy_blast_knockback":
            self.energy_blast_knockback = min(160, self.energy_blast_knockback + 20)
        elif upgrade == "energy_blast_cooldown":
            self.energy_blast_cooldown = max(1, self.energy_blast_cooldown - 1)

    def get_upgrade_options(self):
        # Use base values for display
        if self.level < 10:
            return {
                f"Increase bullet speed ({self.base_bullet_speed} > {self.base_bullet_speed + 2})": "bullet_speed",
                f"Increase bullet damage ({self.base_bullet_damage} > {self.base_bullet_damage + 2})": "bullet_damage",
                f"Increase health ({self.max_health} > {self.max_health + 20})": "health",
                f"Increase firerate ({self.base_bullet_cooldown:.2f}s > {max(0.1, self.base_bullet_cooldown - 0.05):.2f}s)": "bullet_cooldown",
                f"Increase player speed ({self.base_speed} > {self.base_speed + 1})": "speed",
                f"Increase bullet size ({self.base_bullet_size} > {self.base_bullet_size + 2})": "bullet_size",
                f"Increase Health regeneration ({self.base_health_regen} > {self.base_health_regen + 1})": "health_regen",
                f"Increase bullet count ({self.bullet_count} > {self.bullet_count + 1})": "bullet_count",
                f"Increase bullet piercing ({self.bullet_piercing} > {self.bullet_piercing + 1})": "bullet_piercing",
                f"Increase bullet explosion radius ({self.bullet_explosion_radius} > {self.bullet_explosion_radius + 10})": "bullet_explosion_radius"
            } 
        elif self.game.weapon_choice == "mine":
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
            f"Decrease dash cooldown ({self.dash_cooldown} > {max(1, self.dash_cooldown - 1)})": "dash_cooldown",
            f"Increase mine damage ({self.mine_damage} > {self.mine_damage + 10})": "mine_damage",
            f"Increase mine explosion radius ({self.mine_explosion_radius} > {self.mine_explosion_radius + 20})": "mine_explosion_radius",
            f"Decrease mine cooldown ({self.last_mine_drop_cooldown} > {max(0.1, self.last_mine_drop_cooldown - 0.5)})": "mine_cooldown",
            }
        else:
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
            f"Decrease dash cooldown ({self.dash_cooldown} > {max(1, self.dash_cooldown - 1)})": "dash_cooldown",
            f"Increase energy blast damage ({self.energy_blast_damage} > {self.energy_blast_damage + 30})": "energy_blast_damage",
            f"Increase energy blast radius ({self.energy_blast_radius} > {self.energy_blast_radius + 50})": "energy_blast_radius",
            f"Increase energy blast knockback ({self.energy_blast_knockback} > {min(200, self.energy_blast_knockback + 20)}": "energy_blast_knockback",
            f"Decrease energy blast cooldown ({self.energy_blast_cooldown} > {max(1, self.energy_blast_cooldown - 1)})": "energy_blast_cooldown",
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
