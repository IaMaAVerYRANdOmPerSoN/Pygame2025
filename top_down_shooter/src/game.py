import pygame
from pygame.locals import *
from enemy import RangedEnemy, BossEnemy
from pygame import mixer
import time

import glob

# Load all explosion frames into a list
pygame.init()
pygame.display.set_mode((1920, 1080), pygame.FULLSCREEN)

MISSLE_EXPLOSION_FRAMES = [
    pygame.image.load(f).convert_alpha()
    for f in sorted(glob.glob("media/Explosion_missle/*.png"))
]
MISSLE_EXPLOSION_FRAME_COUNT = len(MISSLE_EXPLOSION_FRAMES)
MISSLE_EXPLOSION_ANIMATION_DURATION = 500  # ms

DEATH_EXPLOSION_FRAMES = [
    pygame.image.load(f).convert_alpha()
    for f in sorted(glob.glob("media/Explosion_death/*.png"))
]
DEATH_EXPLOSION_FRAME_COUNT = len(DEATH_EXPLOSION_FRAMES)
DEATH_EXPLOSION_ANIMATION_DURATION = 500  # ms

EXPLOSION_FRAMES = [
    pygame.image.load(f).convert_alpha()
    for f in sorted(glob.glob("media/Explosion/*.png"))
]
EXPLOSION_FRAME_COUNT = len(EXPLOSION_FRAMES)
EXPLOSION_ANIMATION_DURATION = 500  # milliseconds

mixer.init()
# Load sounds
HIT_SOUND = pygame.mixer.Sound("media\hit.wav")
HIT_SOUND.set_volume(0.4)
EXPLOSION_SOUND = pygame.mixer.Sound("media\explosion.wav")
EXPLOSION_SOUND.set_volume(0.15)
SHOOT_SOUND = pygame.mixer.Sound("media\shoot.mp3")
SHOOT_SOUND.set_volume(0.25)

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
        self.pickups = []
        self.active_buffs = []  # Track active timed buffs
        self.background =  pygame.transform.scale(pygame.image.load("media\Background.jpg"), (1920, 1080))
        self.weapon_choice = None
        self.weapon_choosen = False
        self.pickup_chance = None
        self.spawn_enemies = True

    def initialize(self):
        from player import Player
        self.player = Player()
        self.player.game = self
        self.level = 0
        

    def handle_events(self):
        keys = pygame.key.get_pressed()
        move_x = move_y = 0
        if keys[pygame.K_w]:
            move_y -= self.player.speed
        if keys[pygame.K_s]:
            move_y += self.player.speed
        if keys[pygame.K_a]:
            move_x -= self.player.speed
        if keys[pygame.K_d]:
            move_x += self.player.speed
        if move_x or move_y:
            self.player.move(move_x, move_y)

        mouse_buttons = pygame.mouse.get_pressed()
        mouse_pos = pygame.mouse.get_pos()
        if mouse_buttons[0]:  # Left mouse button is held
            self.player.shoot(mouse_pos)
            if self.weapon_choice == "mine":
                self.player.drop_mine()
            elif self.weapon_choice == "energy_blast":
                self.player.energy_blaster.fire(self.player.energy_blaster.firing_pattern)

        # --- Event loop ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.player.dash()
                elif event.key == pygame.K_ESCAPE:
                    self.running = False

        # --- Bullet-Enemy Collisions ---
        INFLATE_DIST = 200

        for bullet in self.player.gun.bullets[:]:
            nearby_enemies = [enemy for enemy in self.enemies
                              if bullet.rect.inflate(INFLATE_DIST, INFLATE_DIST).colliderect(enemy.rect)]
            for enemy in nearby_enemies:
                if enemy.rect.clipline(bullet.prev_pos, bullet.rect.center) or bullet.rect.colliderect(enemy.rect):
                    HIT_SOUND.play()
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
                            self.explosions.append({
                                "pos": bullet.rect.center,
                                "radius": bullet.explosion_radius,
                                "start_time": pygame.time.get_ticks(),
                                "frame": 0
                            })
                            EXPLOSION_SOUND.play()

        # --- Enemy Bullet-Player Collisions ---
        for enemy in self.enemies:
            if isinstance(enemy, RangedEnemy) and hasattr(enemy, "bullets"):
                enemy.bullets = [
                    bullet for bullet in enemy.bullets
                    if not bullet.rect.colliderect(self.player.rect) and self.screen.get_rect().colliderect(bullet.rect)
                ]
                for bullet in enemy.bullets[:]:
                    if bullet.rect.colliderect(self.player.rect):
                        self.player.health -= bullet.damage
                        enemy.bullets.remove(bullet)

        # --- Enemy-Player Collisions & Enemy Updates ---
        for enemy in self.enemies[:]:
            enemy.update()
            if enemy.rect.colliderect(self.player.rect):
                self.player.health -= 12
                enemy.take_damage(enemy.health)
                if self.player.health <= 0:
                    self.running = False
            if enemy.health <= 0:
                pickup = enemy.DropPickup()
                if pickup:
                    self.pickups.append(pickup)
                self.enemies.remove(enemy)
                self.player.score += 100
                # Add death explosion effect
                self.explosions.append({
                    "pos": enemy.rect.center,
                    "radius": 40,  
                    "start_time": pygame.time.get_ticks(),
                    "frame": 0,
                    "type": "death_explosion"
                })
            if hasattr(self, "boss_spawned") and enemy == self.boss:
                self.boss.spawn_missle()

        # --- Level Up and Upgrades ---
        if self.player.score >= self.player.next_level_score[self.player.level]:
            self.player.level += 1
            font = pygame.font.SysFont(None, 48)
            # Only show weapon selection once at level 1, and only if not already chosen
            if self.player.level == 10 and not getattr(self, "weapon_chosen", False):
                upgrade_text = font.render("New Weapon!", True, (255, 255, 0))
                text_rect = upgrade_text.get_rect(center=(self.screen.get_width() // 2, int(self.screen.get_height() * 0.6)))
                self.screen.blit(upgrade_text, text_rect)
                # Let player choose between mines and energy_blast
                font_small = pygame.font.SysFont(None, 36)
                mine_text = font_small.render("1: Unlock Mines", True, (0, 255, 0))
                blast_text = font_small.render("2: Unlock Energy Blast", True, (0, 200, 255))
                y_base = int(self.screen.get_height() * 0.6) + 80
                self.screen.blit(mine_text, (self.screen.get_width() // 2 - 250, y_base))
                self.screen.blit(blast_text, (self.screen.get_width() // 2 + 50, y_base))
                pygame.display.flip()
                waiting = True
                while waiting:
                    for event in pygame.event.get():
                        if event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_1:
                                self.weapon_choice = "mine"
                                waiting = False
                            elif event.key == pygame.K_2:
                                self.weapon_choice = "energy_blast"
                                waiting = False
                        elif event.type == pygame.QUIT:
                            self.running = False
                            waiting = False
                    pygame.time.wait(10)
                self.weapon_chosen = True
            elif self.player.level != 10:
                if self.player.level >= 20 and not hasattr(self, "boss_spawned"):
                    self.boss = BossEnemy()
                    self.boss.player = self.player
                    self.boss.game = self
                    self.enemies.append(self.boss)
                    self.spawn_enemies = False
                    self.boss_spawned = True
                upgrade_text = font.render("Pick an upgrade!", True, (255, 255, 0))
                text_rect = upgrade_text.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2 * 1.8))
                self.screen.blit(upgrade_text, text_rect)
                pygame.display.flip()
                self.player.handle_upgrades(self.screen)

        # --- Pickup Collisions ---
        for pickup in self.pickups[:]:
            if pickup.rect.colliderect(self.player.rect):
                if pickup.kind == "health":
                    self.player.health += 20
                    self.player.health = min(self.player.health, self.player.max_health)
                elif pickup.kind == "damage":
                    self.player.bullet_damage += 20
                    self.active_buffs.append({
                        "type": "damage",
                        "expire_time": time.time() + 5,
                        "amount": 20
                    })
                elif pickup.kind == "speed":
                    self.player.speed += 3
                    self.active_buffs.append({
                        "type": "speed",
                        "expire_time": time.time() + 5,
                        "amount": 3
                    })
                elif pickup.kind == "overload":
                    self.player.health_regen += 5
                    self.player.health += 20
                    self.player.health = min(self.player.health, self.player.max_health)
                    self.player.bullet_damage += 20
                    self.player.speed += 2
                    self.active_buffs.append({
                        "type": "damage",
                        "expire_time": time.time() + 5,
                        "amount": 20
                    })
                    self.active_buffs.append({
                        "type": "speed",
                        "expire_time": time.time() + 5,
                        "amount": 3
                    })
                    if not hasattr(self.player, "_original_bullet_cooldown"):
                        self.player._original_bullet_cooldown = self.player.bullet_cooldown
                    active_cooldown_buffs = [b for b in self.active_buffs if b["type"] == "cooldown"]
                    if len(active_cooldown_buffs) == 0:
                        self.player._original_bullet_cooldown = self.player.bullet_cooldown
                        self.player.bullet_cooldown = 0.03
                    self.active_buffs.append({
                        "type": "cooldown",
                        "expire_time": time.time() + 8,
                    })
                self.pickups.remove(pickup)

        # --- Buff Expiration ---
        now = time.time()
        for buff in self.active_buffs[:]:
            if now >= buff["expire_time"]:
                if buff["type"] == "damage":
                    self.player.bullet_damage = max(self.player.base_bullet_damage, self.player.bullet_damage - buff["amount"])
                elif buff["type"] == "speed":
                    self.player.speed = max(self.player.base_speed, self.player.speed - buff["amount"])
                elif buff["type"] == "cooldown":
                    # Remove this buff
                    self.active_buffs.remove(buff)
                    # If no more cooldown buffs, restore original value
                    if not any(b["type"] == "cooldown" for b in self.active_buffs):
                        if hasattr(self.player, "_original_bullet_cooldown"):
                            self.player.bullet_cooldown = min(self.player._original_bullet_cooldown, self.player.base_bullet_cooldown)
                    continue 
                self.active_buffs.remove(buff)

        # --- Mine Collisions ---
        mines_to_remove = []
        for mine in self.player.mine_layer.mines:
            for enemy in self.enemies:
                if mine.rect.colliderect(enemy.rect):
                    for enemy2 in self.enemies:
                        if mine.rect.inflate(100, 100).colliderect(enemy2.rect):
                            enemy2.take_damage(mine.damage)
                    if mine not in mines_to_remove:
                        mines_to_remove.append(mine)
                    self.explosions.append({
                        "pos": mine.rect.center,
                        "radius": 100,
                        "start_time": pygame.time.get_ticks(),
                        "frame": 0
                    })
                    EXPLOSION_SOUND.play()
                    break  # Only trigger once per mine

        # --- Missle Collisions ---
        if hasattr(self, 'boss'):
            for missle in self.boss.missles[:]:
                if missle.rect.inflate(missle.radius, missle.radius).colliderect(self.player.rect):
                    self.player.health -= missle.damage
                    self.explosions.append({
                        "pos": missle.rect.center,
                        "radius": missle.radius,
                        "start_time": pygame.time.get_ticks(),
                        "frame": 0,
                        "type": "missle_explosion"
                    })
                    self.boss.missles.remove(missle)
                    if self.player.health  <= 0:
                        self.running = False
                elif not self.screen.get_rect().colliderect(missle.rect):
                    self.explosions.append({
                        "pos": missle.rect.center,
                        "radius": missle.radius,
                        "start_time": pygame.time.get_ticks(),
                        "frame": 0,
                        "type": "missle_explosion"
                    })
                    self.boss.missles.remove(missle)

        
        for mine in mines_to_remove:
            if mine in self.player.mines:
                self.player.mines.remove(mine)



    def draw_buff_timers(self, surface):
        font = pygame.font.SysFont(None, 28)
        timer_y = 50  # Start lower to avoid score
        now = time.time()
        grouped_buffs = {}
        for buff in self.active_buffs:
            key = buff["type"]
            time_left = max(0, buff["expire_time"] - now)
            if key in grouped_buffs:
                grouped_buffs[key] = max(grouped_buffs[key], time_left)
            else:
                grouped_buffs[key] = time_left
        for buff_type, time_left in grouped_buffs.items():
            if buff_type == "damage":
                text = font.render(f"Damage Buff: {time_left:.1f}s", True, (255, 80, 80))
            elif buff_type == "speed":
                text = font.render(f"Speed Buff: {time_left:.1f}s", True, (80, 80, 255))
            elif buff_type == "cooldown":
                text = font.render(f"Overload: {time_left:.1f}s", True, (128, 0, 128))
            else:
                text = font.render(f"{buff_type.capitalize()} Buff: {time_left:.1f}s", True, (255, 255, 255))
            surface.blit(text, (10, timer_y))
            timer_y += 32
                
    def draw(self):
        self.screen.blit(self.background, (0, 0))
        self.player.draw(self.screen)
        # Draw mines
        if hasattr(self.player, "mines"):
            for mine in self.player.mines:
                mine.draw(self.screen)
        # Draw energy blast
        if hasattr(self.player, "energy_blast"):
            self.player.energy_blast.draw(self.screen)
        for enemy in self.enemies:
            enemy.draw(self.screen)
            if hasattr(enemy, "bullets"):
                for bullet in enemy.bullets:
                    bullet.draw(self.screen, (255, 0, 0))
        # Draw pickups
        for pickup in self.pickups:
            pickup.draw(self.screen)
        # Draw missiles:
        if hasattr(self, "boss"):
            for missile in self.boss.missles:
                missile.draw(self.screen)
        # Draw explosions
        now = pygame.time.get_ticks()
        for explosion in self.explosions:
            elapsed = now - explosion["start_time"]
            explosion_type = explosion.get("type")
            if explosion_type == "death_explosion":
                frame_idx = int((elapsed / DEATH_EXPLOSION_ANIMATION_DURATION) * DEATH_EXPLOSION_FRAME_COUNT)
                frame_idx = min(frame_idx, DEATH_EXPLOSION_FRAME_COUNT - 1)
                frame_img = DEATH_EXPLOSION_FRAMES[frame_idx]
                scale = explosion["radius"] * 2
                frame_img = pygame.transform.scale(frame_img, (scale, scale))
                rect = frame_img.get_rect(center=explosion["pos"])
                self.screen.blit(frame_img, rect)
            elif explosion_type == "missle_explosion":
                frame_idx = int((elapsed / MISSLE_EXPLOSION_ANIMATION_DURATION) * MISSLE_EXPLOSION_FRAME_COUNT)
                frame_idx = min(frame_idx, MISSLE_EXPLOSION_FRAME_COUNT - 1)
                frame_img = MISSLE_EXPLOSION_FRAMES[frame_idx]
                scale = explosion["radius"] * 2
                frame_img = pygame.transform.scale(frame_img, (scale, scale))
                rect = frame_img.get_rect(center=explosion["pos"])
                self.screen.blit(frame_img, rect)
            else:
                frame_idx = int((elapsed / EXPLOSION_ANIMATION_DURATION) * EXPLOSION_FRAME_COUNT)
                frame_idx = min(frame_idx, EXPLOSION_FRAME_COUNT - 1)
                frame_img = EXPLOSION_FRAMES[frame_idx]
                scale = explosion["radius"] * 2
                frame_img = pygame.transform.scale(frame_img, (scale, scale))
                rect = frame_img.get_rect(center=explosion["pos"])
                self.screen.blit(frame_img, rect)
        # Clean up old explosions
        self.explosions = [
            e for e in self.explosions
            if (e.get("type") == "death_explosion" and now - e["start_time"] < DEATH_EXPLOSION_ANIMATION_DURATION)
            or (e.get("type") != "death_explosion" and now - e["start_time"] < EXPLOSION_ANIMATION_DURATION)
        ]
        # Draw buff timers
        self.draw_buff_timers(self.screen)
        pygame.display.flip()

    def run(self):
        self.initialize()
        
        while self.running:
            self.handle_events()
            self.update()
            self.draw()

    def update(self):
        for bullet in self.player.gun.bullets:
            bullet.update()
        # Remove bullets that go off screen
        self.player.bullets = [b for b in self.player.gun.bullets if 0 <= b.rect.x <= 1920 and 0 <= b.rect.y <= 1080]
        self.player.rect.topleft = self.player.position
        self.player.rect = pygame.Rect(self.player.position[0], self.player.position[1], *self.player.size)
        self.player.rect.clamp_ip(self.screen.get_rect())
        for enemy in self.enemies:
            enemy.update()
            # Call shoot for RangedEnemy
            if hasattr(enemy, "shoot"):
                enemy.shoot()
        self.player.energy_blaster.update(self.enemies)
        if hasattr(self, "boss"):
            for missle in self.boss.missles:
                missle.update(target_x = self.player.position[0], target_y = self.player.position[1])

    def spawn_enemy(self):
        from enemy import Enemy, RangedEnemy
        import random
        x = random.randint(0, self.screen.get_width() - 50)
        y = random.randint(0, self.screen.get_height() - 50)
        if self.player.level >= 12:
            kind = random.choice([
            "enemy",
            "ranged",
            "enemy",
            "ranged",
            "spawner"
            ])
        elif self.player.level >= 7:
            kind = random.choice([
            "enemy",
            "ranged"
            ])
        else:
            kind = "enemy"
        if kind == "enemy":
            enemy = Enemy(x, y, self.enemy_health, self.enemy_speed + 1, chance = self.pickup_chance)
        elif kind == "ranged":
            enemy = RangedEnemy(x, y, self.enemy_health, self.enemy_speed, bullet_speed=3, bullet_damage=5, chance = self.pickup_chance)
        elif kind == "spawner":
            from enemy import SpawnerEnemy
            x = random.randint(0, self.screen.get_width() - 80)
            y = random.randint(0, self.screen.get_height() - 80)
            enemy = SpawnerEnemy(x, y, self.enemy_health * 3, self.enemy_speed / 2, self, chance = self.pickup_chance)
        enemy.player = self.player
        self.enemies.append(enemy)