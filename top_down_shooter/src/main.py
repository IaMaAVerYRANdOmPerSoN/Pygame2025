import pygame
import sys
from game import Game
from score_lib import save_score, get_scores

def show_start_screen(screen):
    font = pygame.font.SysFont(None, 72)
    small_font = pygame.font.SysFont(None, 36)
    input_font = pygame.font.SysFont(None, 48)
    play_button = pygame.Rect(screen.get_width() // 2 - 100, screen.get_height() // 2 + 80, 200, 60)
    name = ""
    input_active = True
    running = True

    while running:
        screen.fill((30, 30, 40))
        title = font.render("Top Down Shooter", True, (255, 255, 0))
        screen.blit(title, (screen.get_width() // 2 - title.get_width() // 2, 100))

        # Name input
        name_label = small_font.render("Enter your name:", True, (255, 255, 255))
        screen.blit(name_label, (screen.get_width() // 2 - 200, screen.get_height() // 2 - 60))
        name_box = pygame.Rect(screen.get_width() // 2 - 150, screen.get_height() // 2 - 10, 300, 50)
        pygame.draw.rect(screen, (255, 255, 255), name_box, 2)
        name_surface = input_font.render(name, True, (255, 255, 255))
        screen.blit(name_surface, (name_box.x + 10, name_box.y + 5))

        # Draw Play button
        pygame.draw.rect(screen, (0, 200, 0), play_button)
        play_text = small_font.render("Play", True, (255, 255, 255))
        screen.blit(play_text, (play_button.centerx - play_text.get_width() // 2, play_button.centery - play_text.get_height() // 2))

        # Draw Score Library
        scores = get_scores()[:5]
        score_title = small_font.render("High Scores:", True, (255, 255, 255))
        screen.blit(score_title, (50, 200))
        for i, (score_name, score_val) in enumerate(scores):
            score_text = small_font.render(f"{i+1}. {score_name}: {score_val}", True, (200, 200, 255))
            screen.blit(score_text, (50, 240 + i * 30))

        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if input_active:
                    if event.key == pygame.K_RETURN:
                        if name.strip():
                            running = False
                    elif event.key == pygame.K_BACKSPACE:
                        name = name[:-1]
                    elif len(name) < 16 and event.unicode.isprintable():
                        name += event.unicode
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                if event.key == pygame.K_TAB:
                    input_active = not input_active
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if play_button.collidepoint(event.pos) and name.strip():
                    running = False
                if name_box.collidepoint(event.pos):
                    input_active = True
    return name.strip()

def main():
    pygame.init()
    screen = pygame.display.set_mode((1280, 720), pygame.FULLSCREEN)
    pygame.display.set_caption("Top Down Shooter")
    while True:
        from enemy import ENEMY_IMAGE, RANGED_ENEMY_IMAGE, enemies_killed_melee, enemies_killed_ranged
        from enemy import SPAWNER_ENEMY_IMAGE, enemies_killed_spawner
        player_name = show_start_screen(screen)
        game = Game(screen)
        game.initialize()
        clock = pygame.time.Clock()
        last_stat_update = pygame.time.get_ticks()
        game.player.energy_blast.draw_callback = game.draw
        game.pickup_chance = 0.1
        game.running = True
        enemies_killed_melee = 0
        enemies_killed_ranged = 0
        enemies_killed_spawner = 0

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
                game.enemy_spawn_rate = max(50, game.enemy_spawn_rate - 0.05)
                game.enemy_health += 3
                game.enemy_speed += 0.03
                game.pickup_chance = game.enemy_spawn_rate * 3.33333333333333333333333333333E-5
                last_stat_update = now

        # --- END SCREEN ---

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

        # Save score
        save_score(player_name, game.player.score)

        # You killed
        killed_text = stat_font.render("You killed:", True, (255, 255, 255))
        killed_rect = killed_text.get_rect(center=(screen.get_width() // 2, 400))
        screen.blit(killed_text, killed_rect)

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

        # Level of the player (middle left)
        level_text = stat_font.render(f"Level: {game.player.level}", True, (255, 255, 255))
        level_rect = level_text.get_rect(midleft=(50, game.screen.get_height() // 2))
        screen.blit(level_text, level_rect)

        # Instructions to exit (middle right)
        instructions_font = pygame.font.Font(None, 40)
        instructions_text = instructions_font.render("Press ESC to exit", True, (255, 255, 255))
        instructions_rect = instructions_text.get_rect(midright=(screen.get_width() - 50, game.screen.get_height() // 2))
        screen.blit(instructions_text, instructions_rect)

        pygame.display.flip()
        # Wait for a key press to exit
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    waiting = False
            clock.tick(60)
        show_start_screen(screen)

if __name__ == "__main__":
    main()