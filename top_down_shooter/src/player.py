import pygame
from pygame.locals import *
import math
import time
import random

class Player:
    def __init__(self):
        from weapons import Gun, MineLayer, EnergyBlaster
        self.gun = Gun("media/Player.png", (0, 0), self, cooldown=0.5, damage=10)
        self.mine_layer = MineLayer("media/mine.png", (0, 0), self, cooldown=2.5, damage=200)
        self.energy_blaster = EnergyBlaster("media/Player.png", (0, 0), self, cooldown=5, damage=120)
        self.game = None
        self.position = [400, 300]
        self.speed = 5
        self.size = (104, 88)
        self.image = pygame.image.load("media\player.png")
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
        self.mine_image = pygame.image.load("media\mine.png")
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
        self.bullet_image = pygame.image.load("media\Player_Bullet.png")
        self.next_level_score = [10, 30, 50, 100] + [1.2**i + 50*i for i in range(5, 999)]  # Example score progression
        self.level = 0  # Player level
        self.energy_blast_cooldown = 5  # seconds
        self.energy_blast_radius = 320  # Radius of the energy blast
        self.energy_blast_damage = 120  # Damage of the energy blast
        self.energy_blast_knockback = 80  # Knockback distance for enemies hit by the blast
        self.angle = 0
        
    def move(self, dx, dy):
        self.position[0] += dx if 0 <= self.position[0] + dx <= 1920 - self.size[0] else 0
        self.position[1] += dy if 0 <= self.position[1] + dy <= 1080 - self.size[1] else 0

    def shoot(self, target_pos):
        self.gun.fire(lambda: self.gun.firing_pattern(target_pos))

    def drop_mine(self):
        self.mine_layer.fire(self.mine_layer.firing_pattern)

    def draw(self, screen):
        # Calculate the center of the player
        player_center = (self.position[0] + self.size[0] // 2, self.position[1] + self.size[1] // 2)
        mouse_x, mouse_y = pygame.mouse.get_pos()
        dx = mouse_x - player_center[0]
        dy = mouse_y - player_center[1]
        self.angle = math.degrees(math.atan2(-dy, dx))  # Negative dy because pygame's y-axis is down

        # Rotate the image
        rotated_image = pygame.transform.rotate(self.image, self.angle + -90)
        rotated_rect = rotated_image.get_rect(center=player_center)

        # Draw the rotated image
        screen.blit(rotated_image, rotated_rect.topleft)

        # Draw weapons
        self.gun.update()
        self.mine_layer.update()
        self.energy_blaster.update(self.game.enemies)
        self.gun.draw(screen)
        self.mine_layer.draw(screen)
        self.energy_blaster.draw(screen)

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
            self.energy_blast_radius += 20
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
            f"Increase energy blast knockback ({self.energy_blast_knockback} > {min(200, self.energy_blast_knockback + 20)})": "energy_blast_knockback",
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
