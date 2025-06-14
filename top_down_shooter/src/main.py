import pygame
import sys
from game import Game

def main():
    pygame.init()
    screen = pygame.display.set_mode((1920, 1080), pygame.FULLSCREEN)
    pygame.display.set_caption("Top Down Shooter")
    game = Game(screen)
    game.initialize()
    clock = pygame.time.Clock()
    last_stat_update = pygame.time.get_ticks()
    while game.running:
        game.handle_events()
        game.update()
        game.draw()
        clock.tick(60)
        if pygame.time.get_ticks() // game.enemy_spawn_rate > getattr(game, 'last_enemy_spawn', -1):
            game.spawn_enemy()
            game.last_enemy_spawn = pygame.time.get_ticks() // 3000
        now = pygame.time.get_ticks()
        if now - last_stat_update >= 3000:
            game.player.health += game.player.health_regen if game.player.health < game.player.max_health else 0
            game.enemy_spawn_rate = max(10, game.enemy_spawn_rate - 0.1)
            game.enemy_health += 1
            game.enemy_speed += 0.02
            last_stat_update = now
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()