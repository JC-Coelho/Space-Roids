import sys
import pygame
import random
from pygame import Vector2
from pygame.transform import rotozoom
from pygame.mixer import Sound

asteroid_images = ["images/asteroid1.png", "images/asteroid2.png", "images/asteroid3.png"]

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
            self.drift = (self.drift + self.forward) / 1.5    # normalized vector addition
        if is_key_pressed[pygame.K_LEFT]:
            self.forward = self.forward.rotate(-2)
        if is_key_pressed[pygame.K_RIGHT]:
            self.forward = self.forward.rotate(2)
        if is_key_pressed[pygame.K_SPACE] and self.can_shoot == 0:
            self.shoot.play()
            self.bullets.append(Bullet(Vector2(self.position), self.forward * 10))
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
        self.position = Vector2(position)
        self.velocity = Vector2(random.randint(-3, 3), random.randint(-3, 3))
        self.image = pygame.image.load(asteroid_images[size])
        self.radius = self.image.get_width() // 2   # Use radius for collisions
        self.size = size

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
        pygame.draw.rect(screen, (255, 255, 255), [self.position.x, self.position.y, 5, 5])


pygame.init()

# Screen size reduced from 800 x 800 (less playable) for laptop development
screen_width = 600  # pixels
screen_height = 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("'Roids")

background = pygame.image.load("images/space.png")
background = pygame.transform.scale(background, (screen_width, screen_height))

game_over = False
ship = Ship((screen.get_width() // 2, screen.get_height() // 2))
asteroids = []
num_asteroids = random.randint(4, 6)    # From Atari '79 original 4-6 asteroids at start

out_of_bounds = [-150, -150, 750, 750]
# Unblock line below if running in 800 x 800 resolution
# out_of_bounds = [-150, -150, 950, 950]

for i in range(num_asteroids):

    # Create asteroids towards edges of the screen using vectors (-> 80%)
    posx, posy = ( random.randint(0, screen.get_width()), \
        random.randint(0, screen.get_height()))
    asteroid_position = (posx, posy)
    asteroid_direction_away_from_screen_center = ( (screen.get_width() // 2 - posx) * 0.8, \
        (screen.get_height() // 2 - posy) * 0.8 )
    asteroid_position += asteroid_direction_away_from_screen_center
    asteroids.append(Asteroid((asteroid_position[0], asteroid_position[1]), 0))

    # Create asteroids
    # asteroids.append(Asteroid( \
    #     ( random.randint(0, screen.get_width()), random.randint(0, screen.get_height()) ) \
    # ))

font = pygame.font.Font("fonts/Alien.ttf", 60)
text_loser = font.render("You Lost!", True, (255, 255, 255))
text_loser_position = ( (screen.get_width() - text_loser.get_width()) // 2, \
    (screen.get_height() - text_loser.get_height()) // 2 )

font2 = pygame.font.Font("fonts/Alien.ttf", 60)   
text_winner = font2.render("You Won!", True, (255, 255, 255))
text_winner_position = ( (screen.get_width() - text_winner.get_width()) // 2, \
    (screen.get_height() - text_winner.get_height()) // 2)

clock = pygame.time.Clock()

while not game_over:
    clock.tick(55)  # 55 fps

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game_over = True

    screen.blit(background, (0, 0))

    if ship is None:
        screen.blit(text_loser, text_loser_position)
        pygame.display.update()
        continue

    if len(asteroids) == 0:
        screen.blit(text_winner, text_winner_position)
        pygame.display.update()
        continue

    # check screen bounds for asteroids
    # pygame.draw.rect(screen, (255, 0, 0), pygame.Rect(out_of_bounds))

    ship.update()
    ship.draw(screen)

    # test for ship collision while looping through asteroids
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

    for b in ship.bullets:
        b.update()
        b.draw(screen)

        # Remove offscreen bullets
        if b.position.x < out_of_bounds[0] \
            or b.position.x > out_of_bounds[2] \
            or b.position.y < out_of_bounds[1] \
            or b.position.y > out_of_bounds[3]:
            if not deadbullets.__contains__(b):
                deadbullets.append(b)

        # Collision checking
        for a in asteroids:
            if a.hit(b.position):
                if not deadbullets.__contains__(b):     # check for duplicates
                    deadbullets.append(b)
                if not deadasteroids.__contains__(a):
                    deadasteroids.append(a)

    for b in deadbullets:
        ship.bullets.remove(b)

    for a in deadasteroids:
        if a.size < 2:
            asteroids.append(Asteroid( a.position, a.size + 1))
            asteroids.append(Asteroid( a.position, a.size + 1))

        asteroids.remove(a)

    

    pygame.display.update()


pygame.quit()
sys.exit(0)