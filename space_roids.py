# pylint: disable=C W0621
import sys
import random
import pygame
from pygame import Vector2
from pygame.transform import rotozoom
from pygame.mixer import Sound

# Load asteroid images
asteroid_images = ["images/asteroid1.png",
                   "images/asteroid2.png", "images/asteroid3.png"]


# Global functions
def blit_rotated(position, image, forward, screen):
    angle = forward.angle_to(Vector2(0, -1))
    rotated_surface = rotozoom(image, angle, 1.0)
    rotated_surface_size = Vector2(rotated_surface.get_size())
    blit_position = position - rotated_surface_size // 2

    screen.blit(rotated_surface, blit_position)


def wrap_position(position, screen):
    x, y = position
    w, h = screen.get_size()
    return Vector2(x % w, y % h)


# Classes
class Surface:
    # Screen manager for different resolutions
    out_of_bounds = []

    def __init__(self, screen):
        self.font = pygame.font.Font("fonts/Alien.ttf", 60)
        self.out_of_bounds = [-150, -150,
                              screen.get_width() + 150, screen.get_height() + 150]

    def update_coords(self, screen):
        self.out_of_bounds = [-150, -150,
                              screen.get_width() + 150, screen.get_height() + 150]

    # Blit message to screen
    def drawText(self, text, screen):
        text = self.font.render(text, True, (255, 255, 255))
        text_position = ((screen.get_width() - text.get_width()) // 2,
                         (screen.get_height() - text.get_height()) // 2)
        screen.blit(text, text_position)


class Ship:
    def __init__(self, position):
        self.shoot = Sound("sounds/shoot.wav")
        self.image = pygame.image.load("images/ship.png")
        self.position = Vector2(position)
        self.forward = Vector2(0, -1)
        self.drift = (0, 0)
        self.bullets = []
        self.can_shoot = 0

    def update(self):
        is_key_pressed = pygame.key.get_pressed()

        if is_key_pressed[pygame.K_UP]:
            self.position += self.forward
            self.drift = (self.drift + self.forward) / \
                1.5    # normalized vector addition
        if is_key_pressed[pygame.K_LEFT]:
            self.forward = self.forward.rotate(-2)
        if is_key_pressed[pygame.K_RIGHT]:
            self.forward = self.forward.rotate(2)
        if is_key_pressed[pygame.K_SPACE] and self.can_shoot == 0:
            self.shoot.play()
            self.bullets.append(
                Bullet(Vector2(self.position), self.forward * 10))
            self.can_shoot = 500

        # Add drift to ship movement
        self.position += self.drift

        # Shooting cooldown time (500 milliseconds)
        if self.can_shoot > 0:
            self.can_shoot -= clock.get_time()  # milliseconds
        else:
            self.can_shoot = 0  # clamp it at 0

    def draw(self, screen):
        self.position = wrap_position(self.position, screen)
        blit_rotated(self.position, self.image, self.forward, screen)


class Asteroid:
    def __init__(self, position, size):
        self.explode = Sound("sounds/explode.mp3")
        self.image = pygame.image.load(asteroid_images[size])
        self.position = Vector2(position)
        self.size = size
        self.velocity = Vector2(random.randint(-3, 3), random.randint(-3, 3))
        self.radius = self.image.get_width() // 2   # Use radius for collisions

    def update(self):
        self.position += self.velocity

        # if self.position.x < out_of_bounds[0] \
        #     or self.position.x > out_of_bounds[2]:
        #     self.velocity.x *= -1

        # if self.position.y < out_of_bounds[1] \
        #     or self.position.y > out_of_bounds[3]:
        #     self.velocity.y *= -1

    def draw(self, screen):
        self.position = wrap_position(self.position, screen)
        blit_rotated(self.position, self.image, self.velocity, screen)

    def hit(self, position):
        if self.position.distance_to(position) <= self.radius:
            self.explode.play()
            return True
        return False


class Bullet:
    def __init__(self, position, velocity):
        self.position = position
        self.velocity = velocity

    def update(self):
        self.position += self.velocity

    def draw(self, screen):
        pygame.draw.rect(screen, (255, 255, 255), [
                         self.position.x, self.position.y, 5, 5])


# Initialise pygame
pygame.init()

# Set screen size here (800 x 800)
screen_width = 600  # pixels
screen_height = 600

screen = pygame.display.set_mode(
    (screen_width, screen_height), pygame.RESIZABLE)
pygame.display.set_caption("'Roids")

background = pygame.image.load("images/space.png")
background = pygame.transform.scale(background, (screen_width, screen_height))

# Instantiate screen manager
surface = Surface(screen)
# out_of_bounds = [-150, -150, screen.get_width() + 150, screen.get_height() + 150]

# Create game elements
ship = Ship((screen.get_width() // 2, screen.get_height() // 2))
asteroids = []
# From Atari '79 original 4-6 asteroids at start
num_asteroids = random.randint(4, 6)

for i in range(num_asteroids):

    # Create asteroids towards edges of the screen using vectors (-> 80%)
    posx, posy = (random.randint(0, screen.get_width()),
                  random.randint(0, screen.get_height()))
    asteroid_position = (posx, posy)
    asteroid_direction_away_from_screen_center = ((screen.get_width() // 2 - posx) * 0.8,
                                                  (screen.get_height() // 2 - posy) * 0.8)
    asteroid_position += asteroid_direction_away_from_screen_center
    asteroids.append(Asteroid((asteroid_position[0], asteroid_position[1]), 0))

    # Create asteroids
    # asteroids.append(Asteroid( \
    #     ( random.randint(0, screen.get_width()), random.randint(0, screen.get_height()) ) \
    # ))

game_over = False
clock = pygame.time.Clock()

# Main loop
while not game_over:
    clock.tick(55)  # 55 fps

    # Event loop
    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            game_over = True

        elif event.type == pygame.VIDEORESIZE:

            surface.update_coords(screen)
            background = pygame.transform.scale(
                background, (screen.get_width(), screen.get_height()))
            pygame.display.update()

    screen.blit(background, (0, 0))

    # Game over
    if ship is None:
        surface.drawText("You Lost!", screen)
        pygame.display.update()
        continue

    # Player win
    if len(asteroids) == 0:
        surface.drawText("You Won!", screen)
        pygame.display.update()
        continue

    # Check screen bounds for asteroids and/or bullets
    # pygame.draw.rect(screen, (255, 0, 0),
    #     pygame.Rect( bounds.out_of_bounds[0],bounds.out_of_bounds[1], \
    #     bounds.out_of_bounds[2], bounds.out_of_bounds[3] ))

    ship.update()
    ship.draw(screen)

    # Test for ship collision while looping through asteroids
    for a in asteroids:
        a.update()
        a.draw(screen)
        if a.hit(ship.position):
            ship = None
            break

    # Break out of main loop
    if ship is None:
        continue

    deadbullets = []
    deadasteroids = []

    # Bullets
    for b in ship.bullets:
        b.update()
        b.draw(screen)

        # Remove offscreen bullets
        if b.position.x < surface.out_of_bounds[0] \
            or b.position.x > surface.out_of_bounds[2] \
            or b.position.y < surface.out_of_bounds[1] \
                or b.position.y > surface.out_of_bounds[3]:
            if b not in deadbullets:
                deadbullets.append(b)

        # Collision checking
        for a in asteroids:
            if a.hit(b.position):
                if b not in deadbullets:     # check for duplicates
                    deadbullets.append(b)
                if a not in deadasteroids:
                    deadasteroids.append(a)

    for b in deadbullets:
        ship.bullets.remove(b)

    # Asteroids
    for a in deadasteroids:
        if a.size < 2:
            asteroids.append(Asteroid(a.position, a.size + 1))
            asteroids.append(Asteroid(a.position, a.size + 1))

        asteroids.remove(a)

    # Update screen
    pygame.display.update()

# Exit
pygame.quit()
sys.exit(0)
