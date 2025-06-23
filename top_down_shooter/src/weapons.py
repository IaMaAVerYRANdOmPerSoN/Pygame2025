import pygame
from operator import add
from time import time
import math
from numpy import sign
from player import Player
import random

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from player import Player

MISSLE_IMAGE = pygame.image.load("media\Enemy_Missile.png")

class Bullet:
    def __init__(
        self,
        x: float,
        y: float,
        target_x: float,
        target_y: float,
        size: int = 10,
        speed: float = 10,
        damage: float = 10,
        count: int = 1,
        pierce: int = 0,
        explosion_radius: float = 0,
        image: pygame.Surface = None
    ) -> None:
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

    def update(self) -> None:
        self.prev_pos = self.rect.center
        self.rect.x += self.velocity[0]
        self.rect.y += self.velocity[1]

    def draw(self, screen: pygame.Surface, color: tuple = (255, 255, 0)) -> None:
        # Draw the bullet image if available, else fallback to rect
        if hasattr(self, "image") and self.image:
            screen.blit(self.image, self.rect)
        else:
            pygame.draw.rect(screen, color, self.rect)


class Mine:
    def __init__(
        self,
        x: float,
        y: float,
        size: int = 50,
        damage: float = 50,
        explosion_radius: float = 100,
        image: pygame.Surface = None
    ) -> None:
        self.position = pygame.Vector2(x, y)
        self.size = size
        self.damage = damage
        self.explosion_radius = explosion_radius
        self.image = image if image else pygame.Surface((size, size))
        self.rect = self.image.get_rect(topleft=(x, y))

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self.image, self.rect.topleft)

    def update(self) -> None:
        self.rect.topleft = (self.position.x, self.position.y)


class EnergyBlast:
    def __init__(
        self,
        player: Player,
        draw_callback: callable = None
    ) -> None:
        self.player = player
        self.active = False
        self.start_time = 0
        self.duration = 0.5  # seconds
        self.radius = 320
        self.current_radius = 0
        self.max_radius = 400
        self.damage = 120
        self.knockback = 80
        self.cooldown = 5
        self.last_used = 0
        self.sound = pygame.mixer.Sound("media/energy_blast.mp3")
        self.sound.set_volume(0.25)
        self.draw_callback = draw_callback
        self.enemies_hit = set()

    def start(
        self,
        cooldown: float = 5,
        radius: float = 500,
        damage: float = 120,
        knockback: float = 200
    ) -> None:
        now = time()
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

    def update(self, enemies: list) -> None:
        if not self.active:
            return
        elapsed = time() - self.start_time
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

    def draw(self, surface: pygame.Surface) -> None:
        if not self.active:
            return
        blast_center = (
            self.player.position[0] + self.player.size[0] // 2,
            self.player.position[1] + self.player.size[1] // 2
        )
        pygame.draw.circle(surface, (70, 130, 255), blast_center, self.current_radius, 5)


class Missile:
    def __init__(
        self,
        distance: float,
        angle: float,
        x: float,
        y: float,
        speed: float = 6,
        radius: float = 80,
        damage: float = 20,
        target = None
    ) -> None:
        self.distance = distance
        self.angle = angle
        self.x, self.y = (x, y)
        self.speed = speed
        self.original_image = pygame.transform.scale(MISSLE_IMAGE.copy(), (30, 30)) # Store the original image
        self.image = self.original_image.copy()
        self.radius = radius
        self.damage = damage
        self.rect = self.image.get_rect(center=(self.x, self.y))
        self.target = target

    def move(self, distance: float, angle: float) -> None:
        radians = math.radians(angle)
        self.x += distance * math.cos(radians)
        self.y += distance * math.sin(radians)

    def update(self, target_x: float, target_y: float) -> None:
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
    
    def draw(self, screen: pygame.Surface) -> None:
        screen.blit(self.image, self.rect)


class Beam:
    def __init__(
        self,
        start_pos: tuple,
        direction: float,
        duration: float,
        color: tuple = (0, 255, 255),
        thickness: int = 12,
        length: int = 1920,
        image: pygame.Surface = None,
        damage: float = 100
    ) -> None:
        self.start_pos = start_pos
        self.direction = direction  # angle in degrees
        self.duration = duration
        self.start_time = time()
        self.color = color
        self.thickness = thickness
        self.length = length  # long enough to cover 1080p diagonally
        self.image = image  # Surface to repeat along the beam
        self.damage = damage

        # Calculate end position based on direction and length
        radians = math.radians(self.direction)
        self.end_pos = (
            self.start_pos[0] + self.length * math.cos(radians),
            self.start_pos[1] + self.length * math.sin(radians)
        )

    def update(self) -> bool:
        # Returns False if the beam should be destroyed
        return not (time() - self.start_time > self.duration)

    def get_line(self) -> tuple:
        return (self.start_pos, self.end_pos)

    def draw(self, screen: pygame.Surface) -> None:
        if self.image:
            # Repeat the image along the beam
            radians = math.radians(self.direction)
            img_width = self.image.get_width()
            img_height = self.image.get_height()
            steps = int(self.length // img_width)
            for i in range(steps):
                x = self.start_pos[0] + i * img_width * math.cos(radians)
                y = self.start_pos[1] + i * img_width * math.sin(radians)
                rotated_img = pygame.transform.rotate(self.image, -self.direction)
                rect = rotated_img.get_rect(center=(x + img_width/2 * math.cos(radians),
                                                    y + img_width/2 * math.sin(radians)))
                screen.blit(rotated_img, rect)
        else:
            # Fallback to drawing a colored line
            pygame.draw.line(screen, self.color, self.start_pos, self.end_pos, self.thickness)
    

class Lightning:
    def __init__(self,
        start_pos: tuple,
        player: Player,
        duration: float,
        chain_count: int,
        chain_range: float,
        damage: float
    ):
        self.start_pos = start_pos
        self.player = player
        self.duration = duration
        self.chain_count = chain_count
        self.chain_range = chain_range
        self.damage = damage
        self.start_time = time()
        self.points = []
        self.hit_enemies = set()
        self.active = True

    def update(self) -> None:
        # Returns False if the lightning should be destroyed
        if time() - self.start_time > self.duration:
            self.active = False
            return False

        # Chain logic
        enemies = [e for e in self.player.game.enemies if e not in self.hit_enemies]
        current_pos = self.start_pos
        self.points = [current_pos]
        for _ in range(self.chain_count):
            if not enemies:
                break
            # Find closest enemy within range
            closest = min(
                enemies,
                key=lambda e: (e.rect.centerx - current_pos[0]) ** 2 + (e.rect.centery - current_pos[1]) ** 2,
                default=None
            )
            if closest:
                dist = ((closest.rect.centerx - current_pos[0]) ** 2 + (closest.rect.centery - current_pos[1]) ** 2) ** 0.5
                if dist <= self.chain_range:
                    self.points.append(closest.rect.center)
                    self.hit_enemies.add(closest)
                    current_pos = closest.rect.center
                    enemies.remove(closest)
                else:
                    break
            else:
                break
        return True

    def draw(self, screen) -> None:
        if len(self.points) > 1:
            lightning_surface = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            for i in range(len(self.points) - 1):
                pygame.draw.line(lightning_surface, (255, 255, 255, 180), self.points[i], self.points[i + 1], 6)
            screen.blit(lightning_surface, (0, 0))


class Aura:
    def __init__(
        self,
        radius : float,
        damage : float,
        color : tuple,
        duration : float,
        x: float,
        y: float,
        alpha : float = 0.3
    ) -> None:
        self.radius = radius
        self.damage = damage
        self.color = color
        self.alpha = alpha
        self.duration = duration
        self.start_time = time()
        self.position = (x, y)

    def update(self) -> bool:
        return not (time() - self.start_time > self.duration)
    
    def draw(self, screen) -> None:
        temp_surface = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        color_with_alpha = (*self.color, int(self.alpha * 255))
        temp_surface.fill((0, 0, 0, 0))
        pygame.draw.circle(
            temp_surface,
            color_with_alpha,
            (self.radius, self.radius),
            self.radius
        )
        pygame.draw.circle(
            temp_surface,
            self.color,
            (self.radius, self.radius),
            self.radius,
            width=3
        )
        screen.blit(
            temp_surface,
            (self.position[0] - self.radius, self.position[1] - self.radius)
        )


class Weapon:
    def __init__(
        self,
        image: str | pygame.Surface | None,
        relative_pos: tuple,
        player: Player | None,
        cooldown: float,
        damage: float
    ) -> None:
        self.player = player
        self.relative_pos = relative_pos
        # Handle NotImplemented or None as a blank image
        if isinstance(image, str):
            self.original_image = pygame.image.load(image)
        elif isinstance(image, pygame.Surface):
            self.original_image = image
        else:
            self.original_image = pygame.Surface((1, 1), pygame.SRCALPHA)
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect()
        self.cooldown = cooldown
        self.last_firing = 0
        self.damage = damage

    def set_player(self, player: Player):
        """Assign the player reference after instantiation."""
        self.player = player

    def fire(self, firing_pattern, *args, **kwargs) -> None:
        now = time()
        then = self.last_firing
        if now - then >= self.cooldown:
            self.last_firing = now
            firing_pattern(*args, **kwargs)

    def move(self) -> None:
        if self.player:
            self.real_pos = list(map(add, self.player.position, self.relative_pos))
            self.image = pygame.transform.rotate(self.original_image, getattr(self.player, "angle", 0))
            self.rect = self.image.get_rect(center=self.real_pos)
        else:
            self.real_pos = self.relative_pos

    def update(self, *args, **kwargs) -> None:
        pass

    def draw(self, screen: pygame.Surface) -> None:
        screen.blit(self.image, self.real_pos if hasattr(self, "real_pos") else self.rect.topleft)
    

class MissileLauncher(Weapon):
    def __init__(
        self,
        image: str,
        realative_pos: tuple,
        player: Player,
        cooldown: float,
        damage: float
    ) -> None:
        super().__init__(image, realative_pos, player, cooldown, damage)
        self.missiles = []

    def firing_pattern(self) -> None:
        # assign the closest enemy at launch
        enemies = self.player.game.enemies
        if enemies:
            closest_enemy = min(
                enemies,
                key=lambda enemy: (enemy.position[0] - self.real_pos[0]) ** 2 + (enemy.position[1] - self.real_pos[1]) ** 2
            )
            ex, ey = closest_enemy.position
            dx = ex - self.real_pos[0]
            dy = ey - self.real_pos[1]
            distance = (dx ** 2 + dy ** 2) ** 0.5
            angle = -pygame.math.Vector2(dx, dy).angle_to((1, 0))
            self.missiles.append(Missile(distance, angle, self.real_pos[0], self.real_pos[1], target=closest_enemy, damage = self.damage))
        else:
            # No enemies, fire straight ahead
            angle = self.player.angle
            self.missiles.append(Missile(0, angle, self.real_pos[0], self.real_pos[1], target=None, damage = self.damage))

    def update(self) -> None:
        for missile in self.missiles[:]:

            if missile.target is not None:
                target_x, target_y = missile.target.position
                missile.update(target_x=target_x, target_y=target_y)
            else:
                missile.update(target_x=missile.x, target_y=missile.y)

    def draw(self, screen: pygame.Surface) -> None:
        super().draw(screen)
        for missile in self.missiles:
            missile.draw(screen)


class BeamCannon(Weapon):
    def __init__(
        self,
        image: str,
        relative_pos: tuple,
        player: Player,
        cooldown: float,
        damage: float,
        duration: float,
    ) -> None:
        super().__init__(image, relative_pos, player, cooldown, damage)
        self.beams = []
        self.duration = duration

    def firing_pattern(self) -> None:
        start_pos = self.player.position
        direction = self.player.angle
        duration = self.duration

        self.beams.append(Beam(start_pos, direction, duration, damage = self.damage))

    def update(self) -> None:
        for beam in self.beams[:]:
            self.beams.remove(beam) if beam.update() == False else None

    def draw(self, screen: pygame.Surface) -> None:
        super().draw(screen)
        for beam in self.beams:
            beam.draw(screen)


class Laser(BeamCannon):
    def __init__(
        self,
        image: str,
        relative_pos: tuple,
        player: Player,
        damage: float,
    ) -> None:
        super().__init__(image, relative_pos, player, cooldown = 0.016, damage = damage, duration = 0.016)


class LightningSpire(Weapon):
    def __init__(
        self,
        image: str,
        relative_pos: tuple,
        player: Player,
        cooldown: float,
        chain_count: int,
        chain_range: float,
        damage: float,
        duration: float = 0.2
    ) -> None:
        super().__init__(image, relative_pos, player, cooldown, damage)
        self.chain_count = chain_count
        self.chain_range = chain_range
        self.duration = duration
        self.lightnings = []

    def firing_pattern(self) -> None:
        # Fire a lightning chain from the spire's position
        start_pos = list(map(add, self.player.position, self.relative_pos))
        lightning = Lightning(
            start_pos=start_pos,
            player=self.player,
            duration=self.duration,
            chain_count=self.chain_count,
            chain_range=self.chain_range,
            damage=self.damage
        )
        self.lightnings.append(lightning)

    def update(self) -> None:
        # Remove finished lightnings
        self.lightnings = [l for l in self.lightnings if l.update()]

    def draw(self, screen: pygame.Surface) -> None:
        super().draw(screen)
        for lightning in self.lightnings:
            lightning.draw(screen)


class AuraGenerator(Weapon):
    def __init__(
        self,
        image: str,
        relative_pos: tuple,
        player: Player,
        cooldown: float,
        duration: float,
        damage: float,
        radius: float,
        AuraColor: tuple|list,
    ) -> None:
        super().__init__(image, relative_pos, player, cooldown, damage)
        self.auras = []
        self.radius = radius
        self.duration = duration
        self.aura_color = AuraColor

    def firing_pattern(self) -> None:
        aura = Aura(self.radius, self.damage, self.aura_color, self.duration, self.relative_pos[0], self.relative_pos[1])
        self.auras.append(aura)

    def update(self) -> None:
        for aura in self.auras[:]:
            if not aura.update():
                self.auras.remove(aura)

    def draw(self, screen: pygame.Surface) -> None:
        super().draw(screen)
        for aura in self.auras:
            aura.draw(screen)


class Gun(Weapon):
    def __init__(
        self,
        image: str | pygame.Surface | None,
        relative_pos: tuple,
        player: Player | None,
        cooldown: float,
        damage: float,
        bullet_speed: float = 15,
        bullet_size: int = 10,
        bullet_count: int = 1,
        bullet_piercing: int = 0,
        bullet_explosion_radius: float = 0,
        bullet_image: pygame.Surface = None
    ):
        super().__init__(image, relative_pos, player, cooldown, damage)
        self.bullet_speed = bullet_speed
        self.bullet_size = bullet_size
        self.bullet_count = bullet_count
        self.bullet_piercing = bullet_piercing
        self.bullet_explosion_radius = bullet_explosion_radius
        self.bullet_image = bullet_image or pygame.image.load("media/Player_Bullet.png")
        self.bullets = []

    def firing_pattern(self, target_pos):
        if not self.player:
            return
        player_center_x = self.player.position[0] + self.player.size[0] // 2
        player_center_y = self.player.position[1] + self.player.size[1] // 2

        angle_to_mouse = math.atan2(
            target_pos[1] - player_center_y,
            target_pos[0] - player_center_x
        )
        spread = 0.15
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
                damage=self.damage,
                count=self.bullet_count,
                pierce=self.bullet_piercing,
                explosion_radius=self.bullet_explosion_radius,
                image=self.bullet_image
            )
            self.bullets.append(bullet)
        try:
            sound = pygame.mixer.Sound("media/shoot.mp3")
            sound.set_volume(0.25)
            sound.play()
        except Exception:
            pass

    def update(self, *args, **kwargs):
        for bullet in self.bullets[:]:
            bullet.update()
            if not (0 <= bullet.rect.x <= 1920 and 0 <= bullet.rect.y <= 1080):
                self.bullets.remove(bullet)

    def draw(self, screen, *args, **kwargs):
        super().draw(screen)
        for bullet in self.bullets:
            bullet.draw(screen)


class MineLayer(Weapon):
    def __init__(
        self,
        image: str | pygame.Surface | None,
        relative_pos: tuple,
        player: Player | None,
        cooldown: float,
        damage: float,
        explosion_radius: float = 300,
        mine_image: pygame.Surface = None
    ):
        super().__init__(image, relative_pos, player, cooldown, damage)
        self.explosion_radius = explosion_radius
        self.mine_image = mine_image or pygame.image.load("media/mine.png")
        self.mines = []

    def firing_pattern(self):
        screen_width, screen_height = 1920, 1080
        mine_x = random.randint(0, screen_width - 50)
        mine_y = random.randint(0, screen_height - 50)
        mine = Mine(
            mine_x,
            mine_y,
            size=50,
            damage=self.damage,
            explosion_radius=self.explosion_radius,
            image=self.mine_image
        )
        self.mines.append(mine)

    def update(self, *args, **kwargs):
        for mine in self.mines:
            mine.update()

    def draw(self, screen, *args, **kwargs):
        super().draw(screen)
        for mine in self.mines:
            mine.draw(screen)


class EnergyBlaster(Weapon):
    def __init__(
        self,
        image: str | pygame.Surface | None,
        relative_pos: tuple,
        player: Player | None,
        cooldown: float,
        damage: float,
        radius: float = 320,
        knockback: float = 80
    ):
        super().__init__(image, relative_pos, player, cooldown, damage)
        self.radius = radius
        self.knockback = knockback
        self.energy_blast = EnergyBlast(player)
        self.cooldown = cooldown

    def firing_pattern(self):
        self.energy_blast.start(
            cooldown=self.cooldown,
            radius=self.radius,
            damage=self.damage,
            knockback=self.knockback
        )

    def update(self, enemies=None, *args, **kwargs):
        if enemies is not None:
            self.energy_blast.update(enemies)

    def draw(self, screen, *args, **kwargs):
        super().draw(screen)
        self.energy_blast.draw(screen)


MAIN_BASE = {
    'Weapons': Gun("media/Player.png", (0, 0), player=None, cooldown=0.5, damage=10),
    'Next': ('MAIN_BEAM', 'MAIN_SPAM', 'MAIN_FUSION')
}

MAIN_BEAM = {
    'Weapons': BeamCannon(None, (0, 10), player=None, cooldown=1, damage=100, duration=0.5),
    'Next': ('MAIN_LASER', 'MAIN_RAILGUN', 'MAIN_BOMB')
}
MAIN_SPAM = {
    'Weapons': Gun("media/Player.png", (0, 0), player=None, cooldown=0.1, damage=1, bullet_count=3),
    'Next': ('MAIN_STORM', 'MAIN_LIGHTNING', 'MAIN_VULCAN')
}
MAIN_FUSION = {
    'Weapons': (
        Gun("media/Player.png", (0, 0), player=None, cooldown=0.5, damage=5),
        BeamCannon(None, (0, 10), player=None, cooldown=1, damage=50, duration=0.5)
    ),
    'Next': ('MAIN_HYBRID', 'MAIN_SPLIT', 'MAIN_ENERGY')
}

MAIN_LASER = {
    'Weapons': Laser(None, (0, 0), player=None, damage=1)
}
MAIN_RAILGUN = {
    'Weapons': BeamCannon(None, (0, 0), player=None, cooldown=1, damage=1000, duration=0.75)
}
MAIN_BOMB = {
    'Weapons': Gun("media/player.png", (0, 0), player=None, cooldown=0.5, damage=500, bullet_size=8, bullet_speed=50, bullet_count=1, bullet_piercing=0, bullet_explosion_radius=500)
}
MAIN_STORM = {
    'Weapons': (
        Gun("media/Player.png", (0, 0), player=None, cooldown=0.1, damage=1, bullet_count=3),
        LightningSpire(None, (0, 0), player=None, cooldown=0.3, chain_count=2, chain_range=800, damage=30)
    )
}
MAIN_LIGHTNING = {
    'Weapons': LightningSpire(None, (0, 0), player=None, cooldown=0.1, chain_count=4, chain_range=1000, damage=50)
}
MAIN_VULCAN = {
    'Weapons': Gun("media/Player.png", (0, 0), player=None, cooldown=0.05, damage=0.8, bullet_count=4)
}
MAIN_HYBRID = {
    'Weapons': (
        Gun("media/Player.png", (0, 0), player=None, cooldown=0.5, damage=6),
        BeamCannon(None, (0, 10), player=None, cooldown=1, damage=60, duration=0.5),
        LightningSpire(None, (0, 0), player=None, cooldown=0.3, chain_count=2, chain_range=600, damage=20)
    )
}
MAIN_SPLIT = {
    'Weapons': (
        BeamCannon(None, (0, 10), player=None, cooldown=0.8, damage=200, duration=0.5),
        LightningSpire(None, (0, 0), player=None, cooldown=0.2, chain_count=3, chain_range=800, damage=20)
    )
}
MAIN_ENERGY = {
    'Weapons': (
        BeamCannon(None, (0, 10), player=None, cooldown=0.8, damage=200, duration=0.5),
        LightningSpire(None, (0, 0), player=None, cooldown=0.2, chain_count=3, chain_range=800, damage=20),
        Laser(None, (0, 0), player=None, damage=0.3)
    )
}