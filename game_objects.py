import pygame
import random
import math

# Initialize the font module for the power-up letters
pygame.font.init()
POWERUP_FONT = pygame.font.Font(None, 20)

class Paddle:
    # ... (This class is unchanged from the previous version)
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.original_width = 100
        self.height = 10
        self.speed = 7
        self.color = (200, 200, 200)
        
        self.width = self.original_width
        self.power_up_timers = {
            'grow': 0,
            'laser': 0,
            'glue': 0
        }
        self.has_laser = False
        self.has_glue = False

        self.rect = pygame.Rect(
            self.screen_width // 2 - self.width // 2,
            self.screen_height - 30,
            self.width,
            self.height
        )

    def reset(self):
        self.rect.x = self.screen_width // 2 - self.original_width // 2
        self.width = self.original_width
        self.rect.width = self.width
        self.has_laser = False
        self.has_glue = False
        for power_up in self.power_up_timers:
            self.power_up_timers[power_up] = 0

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT]:
            self.rect.x += self.speed

        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > self.screen_width:
            self.rect.right = self.screen_width
            
        self._update_power_ups()

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        
    def activate_power_up(self, type):
        duration = 600
        if type == 'grow':
            if self.power_up_timers['grow'] <= 0:
                current_center = self.rect.centerx
                self.width = 150
                self.rect.width = self.width
                self.rect.centerx = current_center
            self.power_up_timers['grow'] = duration
        elif type == 'laser':
            self.has_laser = True
            self.power_up_timers['laser'] = duration
        elif type == 'glue':
            self.has_glue = True
            self.power_up_timers['glue'] = duration
            
    def _update_power_ups(self):
        if self.power_up_timers['grow'] > 0:
            self.power_up_timers['grow'] -= 1
            if self.power_up_timers['grow'] <= 0:
                current_center = self.rect.centerx
                self.width = self.original_width
                self.rect.width = self.width
                self.rect.centerx = current_center
        if self.power_up_timers['laser'] > 0:
            self.power_up_timers['laser'] -= 1
            if self.power_up_timers['laser'] <= 0:
                self.has_laser = False
        if self.power_up_timers['glue'] > 0:
            self.power_up_timers['glue'] -= 1
            if self.power_up_timers['glue'] <= 0:
                self.has_glue = False


class Ball:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.radius = 10
        self.color = (255, 255, 255)
        self.rect = pygame.Rect(0, 0, self.radius * 2, self.radius * 2)

        self.is_glued = False
        self.is_slowed = False
        self.slow_timer = 0
        self.base_speed = 6

        self.trail = []
        self.max_trail = 15

        self.reset()

    def reset(self):
        self.rect.center = (self.screen_width // 2, self.screen_height // 2)
        self.speed_x = self.base_speed * random.choice((1, -1))
        self.speed_y = -self.base_speed
        self.is_glued = False
        self.is_slowed = False
        self.slow_timer = 0
        self.trail.clear()

    def update(self, paddle, launch_ball=False):
        collision_object = None

        if self.is_glued:
            self.rect.centerx = paddle.rect.centerx
            self.rect.bottom = paddle.rect.top
            if launch_ball:
                self.is_glued = False
                self.speed_x = self.base_speed * random.choice((1, -1))
                self.speed_y = -self.base_speed
            return 'playing', None

        if self.is_slowed:
            self.slow_timer -= 1
            if self.slow_timer <= 0:
                self.speed_x *= 2
                self.speed_y *= 2
                self.is_slowed = False

        self.rect.x += self.speed_x
        self.rect.y += self.speed_y

        self.trail.append(self.rect.center)
        if len(self.trail) > self.max_trail:
            self.trail.pop(0)

        if self.rect.top <= 0:
            self.speed_y *= -1
            collision_object = 'wall'
        if self.rect.left <= 0 or self.rect.right >= self.screen_width:
            self.speed_x *= -1
            collision_object = 'wall'

        if self.rect.colliderect(paddle.rect) and self.speed_y > 0:
            if paddle.has_glue:
                self.is_glued = True
            self.speed_y *= -1
            collision_object = 'paddle'

        if self.rect.top > self.screen_height:
            return 'lost', None

        return 'playing', collision_object

    def draw(self, screen):
        for i, (x, y) in enumerate(self.trail):
            alpha = max(30, 255 - i * 15)
            radius = max(2, self.radius - i // 2)
            pygame.draw.circle(screen, (180, 200, 255), (x, y), radius)
        pygame.draw.circle(screen, self.color, self.rect.center, self.radius)

    def activate_power_up(self, type):
        if type == 'stasis' and not self.is_slowed:
            self.speed_x /= 2
            self.speed_y /= 2
            self.is_slowed = True
            self.slow_timer = 600
        elif type == 'hyperdrive':
            self.speed_x *= 1.5
            self.speed_y *= 1.5

class Brick:
    # ... (This class is unchanged from the previous version)
    def __init__(self, x, y, width, height, color):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)


class PowerUp:
    PROPERTIES = {
        'shield':       {'color': (100, 200, 255), 'char': 'S', 'message': 'Shield Activated!'},
        'plasma':       {'color': (255, 0, 255),   'char': 'P', 'message': 'Plasma Ready!'},
        'gravity':      {'color': (173, 216, 230), 'char': 'G', 'message': 'Gravitational Lock!'},
        'stasis':       {'color': (0, 255, 255),   'char': 'T', 'message': 'Stasis Field Active!'},
        'asteroid_hit': {'color': (255, 100, 100), 'char': 'A', 'message': 'Hull Damage!'},
        'hyperdrive':   {'color': (255, 255, 0),   'char': 'H', 'message': 'Hyperdrive!'},
        'extra_life':   {'color': (255, 255, 255), 'char': '+', 'message': 'Extra Pod Online!'}
    }

    def __init__(self, x, y, type):
        self.width = 30
        self.height = 15
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.speed_y = 3
        self.type = type
        self.color = self.PROPERTIES[type]['color']
        self.char = self.PROPERTIES[type]['char']

    def update(self):
        self.rect.y += self.speed_y

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect, border_radius=4)
        char_surface = POWERUP_FONT.render(self.char, True, (0, 0, 0))
        char_rect = char_surface.get_rect(center=self.rect.center)
        screen.blit(char_surface, char_rect)

class Laser:
    # ... (This class is unchanged from the previous version)
    def __init__(self, x, y):
        self.width = 5
        self.height = 15
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.color = (255, 255, 0)
        self.speed_y = -8

    def update(self):
        self.rect.y += self.speed_y

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)

# !!! PHASE: VISUAL EFFECTS !!!
class Particle:
    def __init__(self, x, y, color, min_size, max_size, min_speed, max_speed, gravity):
        self.x = x
        self.y = y
        self.color = color
        self.size = random.randint(min_size, max_size)
        self.gravity = gravity
        angle = random.uniform(0, 360)
        speed = random.uniform(min_speed, max_speed)
        self.vx = speed * math.cos(math.radians(angle))
        self.vy = speed * math.sin(math.radians(angle))

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        self.size -= 0.1 # Particles shrink over time

    def draw(self, screen):
        if self.size > 0:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), int(self.size))

class Firework:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.x = random.randint(0, screen_width)
        self.y = screen_height
        self.vy = -random.uniform(8, 12) # Speed of the rocket
        self.color = (255, 255, 255) # White rocket
        self.exploded = False
        self.particles = []
        self.explosion_y = random.uniform(screen_height * 0.2, screen_height * 0.5)

    def update(self):
        if not self.exploded:
            self.y += self.vy
            if self.y <= self.explosion_y:
                self.exploded = True
                explosion_color = (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
                for _ in range(50): # Create 50 particles on explosion
                    self.particles.append(Particle(self.x, self.y, explosion_color, 2, 4, 1, 4, 0.1))
        else:
            for particle in self.particles[:]:
                particle.update()
                if particle.size <= 0:
                    self.particles.remove(particle)

    def draw(self, screen):
        if not self.exploded:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), 3)
        else:
            for particle in self.particles:
                particle.draw(screen)

    def is_dead(self):
        return self.exploded and not self.particles


class Star:
    def __init__(self, screen_width, screen_height):
        self.x = random.randint(0, screen_width)
        self.y = random.randint(0, screen_height)
        self.radius = random.randint(1, 2)
        self.alpha = random.randint(100, 255)
        self.twinkle_speed = random.uniform(1, 3)

    def update(self):
        self.alpha += self.twinkle_speed
        if self.alpha > 255 or self.alpha < 100:
            self.twinkle_speed *= -1
        self.alpha = max(100, min(255, self.alpha))

    def draw(self, screen):
        color = (255, 255, 255)
        pygame.draw.circle(screen, color, (self.x, self.y), self.radius)

class Meteor:
    def __init__(self, screen_width, screen_height):
        self.x = random.randint(0, screen_width)
        self.y = random.randint(0, screen_height)
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2, 5)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.radius = random.randint(2, 4)
        self.trail = []

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.trail.append((int(self.x), int(self.y)))
        if len(self.trail) > 15:
            self.trail.pop(0)

    def draw(self, screen):
        for i, (tx, ty) in enumerate(self.trail):
            fade = max(50, 255 - i * 15)
            color = (fade, fade, 255)
            pygame.draw.circle(screen, color, (tx, ty), max(1, self.radius - i // 3))
        pygame.draw.circle(screen, (255, 255, 255), (int(self.x), int(self.y)), self.radius)

    def off_screen(self, screen_width, screen_height):
        return (self.x < -20 or self.x > screen_width + 20 or
                self.y < -20 or self.y > screen_height + 20)
# !!! END PHASE: VISUAL EFFECTS !!!
