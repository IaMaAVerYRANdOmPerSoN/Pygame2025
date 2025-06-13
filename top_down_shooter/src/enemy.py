import pygame

class Enemy:
    def __init__(self, x, y, health):
        self.position = (x, y)
        self.health = health
        self.image = pygame.Surface((50, 50))
        self.image.fill((0, 255, 0))
        self.rect = self.image.get_rect(topleft=self.position)
        
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
            if distance != 0:
                speed = 1  # You can adjust the speed as needed
                move_x = speed * dx / distance
                move_y = speed * dy / distance
                self.move(move_x, move_y)