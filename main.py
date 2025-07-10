import pygame
from game_objects import Paddle, Ball, Brick, PowerUp, Laser, Particle, Firework, Star, Meteor
import random
import sys

sound_on_icon = pygame.image.load('sound_on.png')
sound_off_icon = pygame.image.load('sound_off.png')
sound_on_icon = pygame.transform.scale(sound_on_icon, (32, 32))
sound_off_icon = pygame.transform.scale(sound_off_icon, (32, 32))

# Setup (unchanged)
pygame.init()
pygame.mixer.init()
clock = pygame.time.Clock()
screen_width, screen_height = 800, 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("PyGame Arkanoid")

stars = []
meteors = []
# Colors, Fonts, Mute Setup (same as before)
BG_COLOR = pygame.Color(10, 10, 30)
BRICK_COLORS = [(135, 206, 250), (186, 85, 211), (255, 255, 255), (240, 248, 255)]
title_font = pygame.font.Font(None, 70)
game_font = pygame.font.Font(None, 40)
message_font = pygame.font.Font(None, 30)

# Sound Setup with Mute
muted = False
def toggle_mute():
    global muted
    muted = not muted
    if muted:
        for s in [bounce_sound, brick_break_sound, game_over_sound, laser_sound, ambient_music]:
            s.set_volume(0)
    else:
        bounce_sound.set_volume(0.6)
        brick_break_sound.set_volume(0.6)
        game_over_sound.set_volume(0.6)
        laser_sound.set_volume(0.6)
        ambient_music.set_volume(0.5)

try:
    bounce_sound = pygame.mixer.Sound('bounce.wav')
    brick_break_sound = pygame.mixer.Sound('brick_break.wav')
    game_over_sound = pygame.mixer.Sound('game_over.wav')
    laser_sound = pygame.mixer.Sound('laser.wav')
    ambient_music = pygame.mixer.Sound('space_ambient.wav')
    ambient_music.set_volume(0.5)
    ambient_music.play(loops=-1)
    # toggle_mute()
except:
    class Dummy:
        def play(self): pass
        def set_volume(self, v): pass
    bounce_sound = brick_break_sound = game_over_sound = laser_sound = Dummy()

# Game Objects
paddle = Paddle(screen_width, screen_height)
ball = Ball(screen_width, screen_height)

# Brick Wall Function with Level Support
def create_brick_wall(level=1):
    bricks = []
    rows = 4 + level
    cols = 10
    brick_width, brick_height = 75, 20
    padding = 5
    for row in range(rows):
        for col in range(cols):
            x = col * (brick_width + padding) + padding
            y = row * (brick_height + padding) + 50
            color = BRICK_COLORS[row % len(BRICK_COLORS)]
            bricks.append(Brick(x, y, brick_width, brick_height, color))
    return bricks

# Variables
bricks = create_brick_wall()
power_ups, lasers, particles, fireworks = [], [], [], []
game_state = 'title_screen'
score, lives, message_timer = 0, 3, 0
display_message = ""
firework_timer, level = 0, 1

# Game Loop
while True:
    # Events
    for event in pygame.event.get():
        if event.type == pygame.QUIT: pygame.quit(); sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if game_state in ['title_screen', 'you_win', 'game_over']:
                    paddle.reset()
                    ball.reset()
                    level = 1
                    bricks = create_brick_wall(level)
                    score, lives = 0, 3
                    power_ups.clear(); lasers.clear(); particles.clear(); fireworks.clear()
                    game_state = 'playing'
                    ambient_music.play(loops=-1)
                elif ball.is_glued:
                    ball.is_glued = False
            elif event.key == pygame.K_m:
                toggle_mute()
            elif event.key == pygame.K_f and paddle.has_laser:
                lasers.append(Laser(paddle.rect.centerx - 30, paddle.rect.top))
                lasers.append(Laser(paddle.rect.centerx + 30, paddle.rect.top))
                laser_sound.play()

    # Update
    screen.fill(BG_COLOR)

    if game_state == 'title_screen':
        if len(stars) < 100:
            stars.append(Star(screen_width, screen_height))
        for star in stars:
            star.update()
            star.draw(screen)
        if random.random() < 0.08:
            meteors.append(Meteor(screen_width, screen_height))
        for meteor in meteors[:]:
            meteor.update()
            meteor.draw(screen)
            if meteor.off_screen(screen_width, screen_height):
                meteors.remove(meteor)
        screen.blit(title_font.render("ARKANOID", True, (255,255,255)), (screen_width//2 - 130, screen_height//2 - 80))
        screen.blit(game_font.render("Press SPACE to Start", True, (255,255,255)), (screen_width//2 - 140, screen_height//2 + 10))

    elif game_state == 'playing':
        paddle.update()
        keys = pygame.key.get_pressed()
        ball_status, collision = ball.update(paddle, keys[pygame.K_SPACE])

        if ball_status == 'lost':
            lives -= 1
            if lives <= 0:
                game_state = 'game_over'
                game_over_sound.play()
                ambient_music.stop()
            else:
                ball.reset()
                paddle.reset()

        elif collision in ['wall', 'paddle']:
            bounce_sound.play()
            for _ in range(5):
                particles.append(Particle(ball.rect.centerx, ball.rect.centery, (255,255,0), 1,3,1,3,0))

        for brick in bricks[:]:
            if ball.rect.colliderect(brick.rect):
                ball.speed_y *= -1
                score += 10
                bricks.remove(brick)
                brick_break_sound.play()
                for _ in range(10):
                    particles.append(Particle(brick.rect.centerx, brick.rect.centery,
                                              random.choice([(135, 206, 250), (255, 255, 255), (186, 85, 211)]),
                                              1, 3, 1, 3, 0.05))
                if random.random() < 0.4:
                    p_type = random.choice(['shield', 'plasma', 'gravity', 'stasis', 'asteroid_hit', 'hyperdrive', 'extra_life'])
                    power_ups.append(PowerUp(brick.rect.centerx, brick.rect.centery, p_type))
                break

        for power_up in power_ups[:]:
            power_up.update()
            if power_up.rect.top > screen_height:
                power_ups.remove(power_up)
            elif paddle.rect.colliderect(power_up.rect):
                msg = power_up.PROPERTIES[power_up.type]['message']
                display_message = msg
                message_timer = 120
                if power_up.type in ['shield', 'plasma', 'gravity', 'asteroid_hit']:
                    paddle.activate_power_up(power_up.type)
                elif power_up.type in ['stasis', 'hyperdrive']:
                    ball.activate_power_up(power_up.type)
                elif power_up.type == 'extra_life':
                    lives += 1
                power_ups.remove(power_up)

        for laser in lasers[:]:
            laser.update()
            if laser.rect.bottom < 0:
                lasers.remove(laser)
            else:
                for brick in bricks[:]:
                    if laser.rect.colliderect(brick.rect):
                        score += 10
                        bricks.remove(brick)
                        brick_break_sound.play()
                        lasers.remove(laser)
                        break

        if not bricks:
            level += 1
            bricks = create_brick_wall(level)
            ball.reset()
            paddle.reset()

        paddle.draw(screen)
        ball.draw(screen)
        for b in bricks: b.draw(screen)
        for p in power_ups: p.draw(screen)
        for l in lasers: l.draw(screen)

        screen.blit(game_font.render(f"Score: {score}", True, (200, 200, 255)), (10, 10))
        screen.blit(game_font.render(f"Lives: {lives}", True, (200, 200, 255)), (700, 10))
        screen.blit(game_font.render(f"Level: {level}", True, (200, 200, 255)), (360, 10))

    elif game_state == 'you_win' or game_state == 'game_over':
        if len(stars) < 100:
            stars.append(Star(screen_width, screen_height))
        for star in stars:
            star.update()
            star.draw(screen)
        if random.random() < 0.08:
            meteors.append(Meteor(screen_width, screen_height))
        for meteor in meteors[:]:
            meteor.update()
            meteor.draw(screen)
            if meteor.off_screen(screen_width, screen_height):
                meteors.remove(meteor)
        msg = "MISSION COMPLETE!" if game_state == 'you_win' else "     MISSION FAILED"
        screen.blit(game_font.render(msg, True, (255, 255, 255)), (screen_width // 2 - 140, screen_height // 2 - 30))
        screen.blit(game_font.render("Press SPACE to return", True, (255,255,255)), (screen_width//2 - 140, screen_height//2 + 10))

    if message_timer > 0:
        message_timer -= 1
        screen.blit(message_font.render(display_message, True, (200, 200, 255)),
                    (screen_width // 2 - 100, screen_height - 60))
    # Particles
    for p in particles[:]:
        p.update()
        if p.size <= 0:
            particles.remove(p)
    for p in particles:
        p.draw(screen)

    icon = sound_off_icon if muted else sound_on_icon
    screen.blit(icon, (screen_width - 40, screen_height - 40))

    hint = message_font.render("Press M to toggle sound", True, (180, 180, 255))
    screen.blit(hint, (10, screen_height - 30))
    pygame.display.flip()
    clock.tick(60)
