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
            game.enemy_spawn_rate = max(10, game.enemy_spawn_rate - 0.05)
            game.enemy_health += 4
            game.enemy_speed += 0.02
            last_stat_update = now

    # --- END SCREEN ---
    from enemy import ENEMY_IMAGE, RANGED_ENEMY_IMAGE, enemies_killed_melee, enemies_killed_ranged
    from enemy import SPAWNER_ENEMY_IMAGE, enemies_killed_spawner
    screen.fill((0, 0, 0))
    # Large bold font for "Game Over" and stats
    title_font = pygame.font.Font(None, 160)
    stat_font = pygame.font.Font(None, 120)
    label_font = pygame.font.Font(None, 60)

    # Game Over
    text = title_font.render("Game Over", True, (255, 0, 0))
    text_rect = text.get_rect(center=(screen.get_width() // 2, 120))
    screen.blit(text, text_rect)

    # Score (large)
    score_text = stat_font.render(f"Score: {game.player.score}", True, (255, 255, 0))
    score_rect = score_text.get_rect(center=(screen.get_width() // 2, 300))
    screen.blit(score_text, score_rect)

    # You killed
    killed_text = stat_font.render("You killed:", True, (255, 255, 255))
    killed_rect = killed_text.get_rect(center=(screen.get_width() // 2, 400))
    screen.blit(killed_text, killed_rect)

    # Melee enemies killed
    # Melee enemies killed (centered)
    melee_text = stat_font.render(f"{enemies_killed_melee}", True, (255, 255, 255))
    x_font = label_font.render("x", True, (255, 255, 255))
    enemy_img = ENEMY_IMAGE
    total_width = (
        melee_text.get_width() +
        x_font.get_width() + 20 +
        enemy_img.get_width() + 20
    )
    melee_y = 500
    start_x = (screen.get_width() - total_width) // 2

    screen.blit(melee_text, (start_x, melee_y))
    x_rect = x_font.get_rect(midleft=(start_x + melee_text.get_width() + 20, melee_y + melee_text.get_height() // 2))
    screen.blit(x_font, x_rect)
    enemy_img_rect = enemy_img.get_rect(midleft=(x_rect.right + 20, melee_y + melee_text.get_height() // 2))
    screen.blit(enemy_img, enemy_img_rect)

    # Ranged enemies killed (centered)
    ranged_text = stat_font.render(f"{enemies_killed_ranged}", True, (255, 255, 255))
    x2_font = label_font.render("x", True, (255, 255, 255))
    ranged_img = RANGED_ENEMY_IMAGE
    total_width2 = (
        ranged_text.get_width() +
        x2_font.get_width() + 20 +
        ranged_img.get_width() + 20
    )
    ranged_y = 700
    start_x2 = (screen.get_width() - total_width2) // 2

    screen.blit(ranged_text, (start_x2, ranged_y))
    x2_rect = x2_font.get_rect(midleft=(start_x2 + ranged_text.get_width() + 20, ranged_y + ranged_text.get_height() // 2))
    screen.blit(x2_font, x2_rect)
    ranged_img_rect = ranged_img.get_rect(midleft=(x2_rect.right + 20, ranged_y + ranged_text.get_height() // 2))
    screen.blit(ranged_img, ranged_img_rect)

    # Spawner enemies killed (centered)
    spawner_text = stat_font.render(f"{enemies_killed_spawner}", True, (255, 255, 255))
    x3_font = label_font.render("x", True, (255, 255, 255))
    spawner_img = SPAWNER_ENEMY_IMAGE
    total_width3 = (
        spawner_text.get_width() +
        x3_font.get_width() + 20 +
        spawner_img.get_width() + 20
    )
    spawner_y = 900
    start_x3 = (screen.get_width() - total_width3) // 2

    screen.blit(spawner_text, (start_x3, spawner_y))
    x3_rect = x3_font.get_rect(midleft=(start_x3 + spawner_text.get_width() + 20, spawner_y + spawner_text.get_height() // 2))
    screen.blit(x3_font, x3_rect)
    spawner_img_rect = spawner_img.get_rect(midleft=(x3_rect.right + 20, spawner_y + spawner_text.get_height() // 2))
    screen.blit(spawner_img, spawner_img_rect)

    pygame.display.flip()
    # Wait for a key press to exit
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                waiting = False
        clock.tick(60)
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()