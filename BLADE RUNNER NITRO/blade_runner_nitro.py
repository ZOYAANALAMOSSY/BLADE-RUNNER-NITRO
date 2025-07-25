import pygame
import random
import os 
import sys

pygame.init()

# Screen setup
WIDTH, HEIGHT = 960, 480
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("BLADE RUNNER NITRO")
clock = pygame.time.Clock()

# Load and scale image assets
def load_image(name, size=None):
    path = os.path.join(r"C:\Users\zoyaa\OneDrive\Desktop\BLADE RUNNER NITRO", name)
    image = pygame.image.load(path).convert_alpha()
    if size:
        image = pygame.transform.scale(image, size)
    return image

# Load assets
background_tile = load_image("background_tile.png")
tile_width = background_tile.get_width()
tiles_x = WIDTH // tile_width + 2

ninja_run = [load_image("ninja_run1.png", (60, 80)), load_image("ninja_run2.png", (60, 80))]
ninja_star_img = load_image("ninja_star.png", (32, 32))
obstacle_img = load_image("obstacle1.png", (50, 50))
enemy_ninja_img = load_image("enemy_ninja.png", (50, 80))
explosion_img = load_image("explosion.png", (50, 50))
heart_icon = load_image("heart.png", (30, 30))
heart_powerup_img = load_image("heart_powerup.png", (30, 30))

# Game constants
GROUND_Y = HEIGHT - 220
SPAWN_DISTANCE = 120
ninja_x, ninja_y = 50, GROUND_Y
ninja_index = 0
jumping = False
jump_velocity = 0
jump_count = 0
stars = []
enemy_stars = []
obstacles = []
explosions = []
background_x = 0
score = 0
frame_count = 0
font = pygame.font.SysFont(None, 36)
game_over = False
last_spawn_x = 0
star_cooldown = 0
health = 3
heart_powerups = []
space_held = False
paused = False
in_main_menu = True

class EnemyNinja:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.cooldown = random.randint(60, 180)

    def update(self):
        self.x -= 5
        self.cooldown -= 1
        if self.cooldown <= 0:
            self.cooldown = random.randint(90, 150)
            return [self.x, self.y + 20]
        return None

enemy_ninjas = []

# Draw background
def draw_background():
    global background_x
    screen.fill((100, 200, 255))
    background_x = (background_x - 3) % tile_width
    for i in range(tiles_x):
        screen.blit(background_tile, (i * tile_width - background_x, 2))

# Draw ninja
def draw_ninja():
    global ninja_index
    ninja_index = (ninja_index + 1) % 20
    frame = ninja_run[ninja_index // 10]
    screen.blit(frame, (ninja_x, ninja_y))

# Fire star toward mouse cursor
def fire_star():
    mouse_x, mouse_y = pygame.mouse.get_pos()
    dx, dy = mouse_x - (ninja_x + 30), mouse_y - (ninja_y + 20)
    dist = max(1, (dx ** 2 + dy ** 2) ** 0.5)
    vel_x = dx / dist * 10
    vel_y = dy / dist * 10
    stars.append({'pos': [ninja_x + 30, ninja_y + 20], 'vel': [vel_x, vel_y]})

# Draw and update stars
def draw_stars():
    for star in stars[:]:
        star['pos'][0] += star['vel'][0]
        star['pos'][1] += star['vel'][1]
        if star['pos'][0] > WIDTH or star['pos'][1] > HEIGHT or star['pos'][0] < 0 or star['pos'][1] < 0:
            stars.remove(star)
        else:
            screen.blit(ninja_star_img, star['pos'])

# Draw enemy stars
def draw_enemy_stars():
    for star in enemy_stars[:]:
        star[0] -= 10
        if star[0] < -32:
            enemy_stars.remove(star)
        else:
            screen.blit(ninja_star_img, star)

# Spawn obstacles, enemies, and rare heart

def spawn_obstacle():
    global last_spawn_x
    spawn_rate = 6 + frame_count // 1000
    if frame_count - last_spawn_x > SPAWN_DISTANCE and random.randint(0, 100) < spawn_rate:
        if random.choice([True, False]):
            obstacles.append([WIDTH, GROUND_Y + 30])
            if random.random() < 0.5:
                obstacles.append([WIDTH + 60, GROUND_Y + 30])
        else:
            enemy_ninjas.append(EnemyNinja(WIDTH, GROUND_Y))
        last_spawn_x = frame_count

    # Rare heart spawn
    if random.randint(0, 1000) < 2:
        heart_powerups.append([WIDTH, GROUND_Y + 40])

# Draw and update obstacles
def draw_obstacles():
    for obs in obstacles[:]:
        obs[0] -= 7
        if obs[0] < -50:
            obstacles.remove(obs)
        else:
            screen.blit(obstacle_img, obs)

# Draw and update enemies
def draw_enemy_ninjas():
    for enemy in enemy_ninjas[:]:
        star = enemy.update()
        if star:
            enemy_stars.append(star)
        if enemy.x < -50:
            enemy_ninjas.remove(enemy)
        else:
            screen.blit(enemy_ninja_img, (enemy.x, enemy.y))

# Draw explosions
def draw_explosions():
    for explosion in explosions[:]:
        x, y, timer = explosion
        screen.blit(explosion_img, (x, y))
        explosion[2] -= 1
        if explosion[2] <= 0:
            explosions.remove(explosion)

# Draw heart powerups
def draw_heart_powerups():
    global health
    for heart in heart_powerups[:]:
        heart[0] -= 5
        if heart[0] < -30:
            heart_powerups.remove(heart)
        else:
            screen.blit(heart_powerup_img, heart)
            if pygame.Rect(ninja_x, ninja_y, 60, 80).colliderect(pygame.Rect(heart[0], heart[1], 30, 30)):
                health += 1
                heart_powerups.remove(heart)

# Draw health hearts
def draw_hearts():
    for i in range(health):
        screen.blit(heart_icon, (WIDTH - 40 * (i + 1), 10))

# Check collisions
def check_collisions():
    global score, game_over, health
    ninja_rect = pygame.Rect(ninja_x, ninja_y, 60, 80)

    for star in stars[:]:
        star_rect = pygame.Rect(star['pos'][0], star['pos'][1], 32, 32)
        for enemy in enemy_ninjas[:]:
            enemy_rect = pygame.Rect(enemy.x, enemy.y, 50, 80)
            if star_rect.colliderect(enemy_rect):
                explosions.append([enemy.x, enemy.y, 5])
                if star in stars: stars.remove(star)
                if enemy in enemy_ninjas: enemy_ninjas.remove(enemy)
                score += 20
                break

    for obs in obstacles[:]:
        if ninja_rect.colliderect(pygame.Rect(obs[0], obs[1], 50, 50)):
            health -= 1
            obstacles.remove(obs)
            if health <= 0:
                game_over = True
    for enemy in enemy_ninjas[:]:
        if ninja_rect.colliderect(pygame.Rect(enemy.x, enemy.y, 50, 80)):
            health -= 1
            enemy_ninjas.remove(enemy)
            if health <= 0:
                game_over = True
    for est in enemy_stars[:]:
        if ninja_rect.colliderect(pygame.Rect(est[0], est[1], 32, 32)):
            enemy_stars.remove(est)
            health -= 1
            if health <= 0:
                game_over = True

# Show game over screen
def show_game_over():
    text1 = font.render("YOU DIED", True, (255, 0, 0))
    text2 = font.render("Press ESC to Quit", True, (255, 255, 255))
    text3 = font.render("Press R to Restart", True, (255, 255, 255))
    screen.blit(text1, (WIDTH // 2 - 60, HEIGHT // 2 - 40))
    screen.blit(text2, (WIDTH // 2 - 110, HEIGHT // 2))
    screen.blit(text3, (WIDTH // 2 - 120, HEIGHT // 2 + 40))


# Show main menu
def show_main_menu():
    title = font.render("BLADE RUNNER NITRO", True, (255, 255, 0))
    prompt = font.render("Press SPACE to Start", True, (255, 255, 255))
    controls = font.render("Controls: Space = Jump, F = Throw Star, P = Pause", True, (255, 255, 255))
    screen.blit(title, (WIDTH // 2 - 100, HEIGHT // 2 - 60))
    screen.blit(prompt, (WIDTH // 2 - 120, HEIGHT // 2))
    screen.blit(controls, (WIDTH // 2 - 200, HEIGHT // 2 + 40))

# Main game loop
running = True
while running:
    draw_background()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if in_main_menu and event.key == pygame.K_SPACE:
                in_main_menu = False
            elif event.key == pygame.K_p:
                paused = not paused
            elif event.key == pygame.K_f and star_cooldown == 0 and not game_over and not in_main_menu:
                fire_star()
                star_cooldown = 0

    if in_main_menu:
        show_main_menu()

    elif not game_over and not paused:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE] and not space_held:
            if jump_count < 2:
                jump_velocity = -15
                jumping = True
                jump_count += 1
            space_held = True
        elif not keys[pygame.K_SPACE]:
            space_held = False

        if jumping:
            ninja_y += jump_velocity
            jump_velocity += 1
            if ninja_y >= GROUND_Y:
                ninja_y = GROUND_Y
                jumping = False
                jump_count = 0

        draw_obstacles()
        draw_enemy_ninjas()
        draw_stars()
        draw_enemy_stars()
        draw_ninja()
        draw_explosions()
        draw_heart_powerups()
        draw_hearts()
        spawn_obstacle()
        check_collisions()

        score_text = font.render(f"Score: {score}", True, (255, 255, 255))
        tip_text = font.render("Press F to throw stars toward your mouse!", True, (255, 255, 255))
        screen.blit(score_text, (10, 10))
        screen.blit(tip_text, (10, 40))

        frame_count += 5
        if star_cooldown > 0:
            star_cooldown -= 1

    elif game_over:
        draw_obstacles()
        draw_enemy_ninjas()
        draw_stars()
        draw_enemy_stars()
        draw_ninja()
        draw_explosions()
        draw_heart_powerups()
        draw_hearts()
        show_game_over()

        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            pygame.quit()
            sys.exit()

        elif keys[pygame.K_r]:
            ninja_y = GROUND_Y
            jumping = False
            jump_velocity = 0
            jump_count = 0
            stars.clear()
            enemy_stars.clear()
            obstacles.clear()
            enemy_ninjas.clear()
            explosions.clear()
            heart_powerups.clear()
            score = 0
            frame_count = 0
            health = 3
            game_over = False
            paused = False


    pygame.display.flip()
    clock.tick(30)

















