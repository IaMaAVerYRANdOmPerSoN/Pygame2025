import pygame

class Pickup:
    def __init__(self, x, y, size=(50, 50), image=None, kind=None):
        self.position = pygame.Vector2(x, y)
        self.size = size
        self.image = pygame.transform.scale(image, (64, 64)) if image else pygame.Surface(size)
        self.rect = self.image.get_rect(center=(x, y))
        self.kind = kind

    def draw(self, surface):
        surface.blit(self.image, self.rect.topleft)

    def update(self):
        self.rect.topleft = (self.position.x, self.position.y)