import pygame
import sys
from game import Game

def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Top Down Shooter")
    game = Game(screen)
    game.initialize()
    clock = pygame.time.Clock()
    while game.running:
        game.handle_events()
        game.update()
        game.draw()
        clock.tick(60)
        if pygame.time.get_ticks() // 3000 > getattr(game, 'last_enemy_spawn', -1):
            game.spawn_enemy()
            game.last_enemy_spawn = pygame.time.get_ticks() // 3000
            game.player.health += game.player.health_regen # Regenerate player health every 3 seconds
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()