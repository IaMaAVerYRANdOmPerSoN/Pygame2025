def load_image(filepath):
    """Load an image from the given filepath."""
    import pygame
    image = pygame.image.load(filepath)
    return image

def draw_text(surface, text, position, font, color=(255, 255, 255)):
    """Draw text on the given surface at the specified position."""
    text_surface = font.render(text, True, color)
    surface.blit(text_surface, position)

def check_collision(rect1, rect2):
    """Check if two rectangles collide."""
    return rect1.colliderect(rect2)

def clamp(value, min_value, max_value):
    """Clamp a value between a minimum and maximum."""
    return max(min_value, min(value, max_value))