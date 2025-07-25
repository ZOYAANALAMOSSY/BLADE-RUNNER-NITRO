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
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_image(name, size=None):
    path = os.path.join(BASE_DIR, name)
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
enemies_img = pygame.image.load("enemies.png")
enemies_img = pygame.transform.scale(enemies_img, (50, 70))  # Resize enemy
enemies_img = pygame.transform.flip(enemies_img, True, False)
explosion_img = load_image("explosion.png", (50, 50))
heart_icon = load_image("heart.png", (30, 30))
heart_powerup_img = load_image("heart_powerup.png", (30, 30))
bomb_img = load_image("bomb.png", (30, 30))  



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
bombs = []
bomb_count = 0
thrown_bombs = []
player_name = ""
show_name_input = True
input_text = ""
leaderboard = []


class EnemyNinja:
    def __init__(self, x, y):
        self.x = x
        self.base_y = y
        self.y = y
        self.health = 3
        self.width = enemies_img.get_width()
        self.height = enemies_img.get_height()
        self.exploding = False
        self.explosion_timer = 0
        self.cooldown = random.randint(100, 200)
        self.jump_velocity = 0
        self.jumping = False
        self.jump_cooldown = 0

    def draw(self, screen):
        if self.exploding:
            screen.blit(explosion_img, (self.x, self.y))
            self.explosion_timer -= 1
            if self.explosion_timer <= 0:
                self.exploding = False
        else:
            screen.blit(enemies_img, (self.x, self.y))
            self.draw_health_bar(screen)

    def draw_health_bar(self, screen):
        pygame.draw.rect(screen, (255, 0, 0), (self.x, self.y - 10, 30, 5))
        pygame.draw.rect(screen, (0, 255, 0), (self.x, self.y - 10, 10 * self.health, 5))

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def check_dodge(self):
        for star in stars:
            star_x, star_y = star['pos']
            if abs(star_x - self.x) < 100 and abs(star_y - self.y) < 50:
                if self.jump_cooldown == 0 and not self.jumping:
                    self.jumping = True
                    self.jump_velocity = -15
                    self.jump_cooldown = 60  # 2-second cooldown (30 FPS)
                    break

    def update(self):
        self.x -= 5

        if self.jump_cooldown > 0:
            self.jump_cooldown -= 1

        self.check_dodge()

        # Handle jumping
        if self.jumping:
            self.y += self.jump_velocity
            self.jump_velocity += 1
            if self.y >= self.base_y:
                self.y = self.base_y
                self.jumping = False

        # Handle throwing stars
        self.cooldown -= 1
        if self.cooldown <= 0 and random.random() < 0.1:
            self.cooldown = random.randint(100, 200)
            return [self.x, self.y]
        return None

# Replace old enemy list logic with EnemyNinja objects
enemies = []


# Draw background
def draw_background():
    global background_x
    screen.fill((100, 200, 255))
    background_x = (background_x + 5) % tile_width
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
        star[0] -= 13
        if star[0] < -32:
            enemy_stars.remove(star)
        else:
            screen.blit(ninja_star_img, star)

# Spawn obstacles, enemies, and rare heart

def spawn_obstacle():
    global last_spawn_x
    spawn_rate = 2 + frame_count // 1500  # Slightly lower chance
    if frame_count - last_spawn_x > SPAWN_DISTANCE and random.randint(0, 100) < spawn_rate:
        if random.random() < 0.4:  # 40% chance of obstacle
            obstacles.append([WIDTH, GROUND_Y + 30])
            if random.random() < 0.5:
                obstacles.append([WIDTH + 60, GROUND_Y + 30])
        else:
            enemies.append(EnemyNinja(WIDTH, GROUND_Y))
        last_spawn_x = frame_count

    # Rare heart spawn
    if random.randint(0, 400) < 1:
        heart_powerups.append([WIDTH, GROUND_Y + 40])

    # Spawn bombs (rare)
    if random.randint(0, 300) == 0:  # rarer than heart (1 in 300 frames)
        bombs.append([WIDTH, GROUND_Y + 40])



def draw_bomb_collectibles():
    global bomb_count
    for bomb in bombs[:]:
        bomb[0] -= 5
        if bomb[0] < -30:
            bombs.remove(bomb)
        else:
            screen.blit(bomb_img, bomb)
            ninja_rect = pygame.Rect(ninja_x, ninja_y, 60, 80)
            bomb_rect = pygame.Rect(bomb[0], bomb[1], 30, 30)
            if ninja_rect.colliderect(bomb_rect):
                bomb_count += 1
                bombs.remove(bomb)

def draw_bomb_counter():
    for i in range(bomb_count):
        screen.blit(bomb_img, (10 + i * 35, 100))

bomb_spawn_y = HEIGHT - 150


# Draw and update obstacles
def draw_obstacles():
    for obs in obstacles[:]:
        obs[0] -= 9
        if obs[0] < -50:
            obstacles.remove(obs)
        else:
            screen.blit(obstacle_img, obs)

# Draw and update enemies
def draw_enemies():
    for enemy in enemies[:]:
        star = enemy.update()
        if star:
            enemy_stars.append(star)
        if enemy.x < -50:
            enemies.remove(enemy)
        else:
            enemy.draw(screen)


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
        if heart[0] < -30:
            heart_powerups.remove(heart)
        else:
            screen.blit(heart_powerup_img, heart)
        if pygame.Rect(ninja_x, ninja_y, 60, 80).colliderect(pygame.Rect(heart[0], heart[1], 30, 30)):
            if health < 5:
                health += 1
            heart_powerups.remove(heart)


# Draw health hearts
def draw_hearts():
    for i in range(health):
        screen.blit(heart_icon, (WIDTH - 40 * (i + 1), 10))


def draw_bomb_collectibles():
    global bomb_count
    for bomb in bombs[:]:
        bomb[0] -= 5
        if bomb[0] < -30:
            bombs.remove(bomb)
        else:
            screen.blit(bomb_img, bomb)
            ninja_rect = pygame.Rect(ninja_x, ninja_y, 60, 80)
            bomb_rect = pygame.Rect(bomb[0], bomb[1], 30, 30)
            if ninja_rect.colliderect(bomb_rect):
                bomb_count += 1
                bombs.remove(bomb)


# Check collisions
def check_collisions():
    global score, game_over, health
    ninja_rect = pygame.Rect(ninja_x, ninja_y, 60, 80)

    for star in stars[:]:
        star_rect = pygame.Rect(star['pos'][0], star['pos'][1], 32, 32)
        for enemy in enemies[:]:
            enemy_rect = pygame.Rect(enemy.x, enemy.y, 50, 80)
            if star_rect.colliderect(enemy_rect):
                explosions.append([enemy.x, enemy.y, 5])
                if star in stars:
                    stars.remove(star)
                    if enemy in enemies:
                        enemy.health -= 1
                        if enemy.health <= 0:
                            enemies.remove(enemy)
                            score += 20


    for obs in obstacles[:]:
        if ninja_rect.colliderect(pygame.Rect(obs[0], obs[1], 50, 50)):
            health -= 1
            obstacles.remove(obs)
            if health <= 0:
                game_over = True
    for enemy in enemies[:]:
        if ninja_rect.colliderect(pygame.Rect(enemy.x, enemy.y, 50, 80)):
            health -= 1
            enemies.remove(enemy)
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
    text3 = font.render("Press R to Retry", True, (255, 255, 255))
    text4 = font.render("Press M for Menu", True, (255, 255, 255))
    screen.blit(text1, (WIDTH // 2 - 60, HEIGHT // 2 - 60))
    screen.blit(text2, (WIDTH // 2 - 110, HEIGHT // 2))
    screen.blit(text3, (WIDTH // 2 - 110, HEIGHT // 2 + 40))
    screen.blit(text4, (WIDTH // 2 - 110, HEIGHT // 2 + 80))



# Show main menu
def show_main_menu():
    title = font.render("BLADE RUNNER NITRO", True, (255, 255, 0))
    screen.blit(title, (WIDTH // 2 - 100, HEIGHT // 2 - 100))
    if show_name_input:
        prompt = font.render("Enter Name: " + input_text, True, (255, 255, 255))
        screen.blit(prompt, (WIDTH // 2 - 140, HEIGHT // 2 - 40))
    else:
        prompt = font.render("Press SPACE to Start", True, (255, 255, 255))
        screen.blit(prompt, (WIDTH // 2 - 120, HEIGHT // 2))
        controls = font.render("Controls: Space = Jump, F = Throw Star, P = Pause", True, (255, 255, 255))
        screen.blit(controls, (WIDTH // 2 - 200, HEIGHT // 2 + 40))
        lb_title = font.render("LEADERBOARD", True, (255, 215, 0))
        screen.blit(lb_title, (WIDTH - 250, 30))
        for idx, entry in enumerate(leaderboard[-5:][::-1]):
            entry_text = font.render(f"{entry[0]}: {entry[1]}", True, (255, 255, 255))
            screen.blit(entry_text, (WIDTH - 250, 70 + idx * 30))

def draw_thrown_bombs():
    global enemies
    for bomb in thrown_bombs[:]:
        bomb[0] += 12
        screen.blit(bomb_img, (bomb[0] - 15, bomb[1] - 15))  # center it

        # Bomb collision with enemies
        for enemy in enemies[:]:
            enemy_rect = pygame.Rect(enemy.x, enemy.y, 50, 80)
            if pygame.Rect(bomb[0], bomb[1], 30, 30).colliderect(enemy_rect):
                explosions.append([enemy.x, enemy.y, 6])
                enemies.remove(enemy)

        # Remove bomb if off screen
        if bomb[0] > WIDTH:
            thrown_bombs.remove(bomb)


# Main game loop
running = True
while running:
    draw_background()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if in_main_menu:
                if show_name_input:
                    if event.key == pygame.K_RETURN:
                        if input_text.strip():
                            player_name = input_text.strip()
                            show_name_input = False
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    else:
                        if len(input_text) < 12 and event.unicode.isprintable():
                            input_text += event.unicode
                elif event.key == pygame.K_SPACE:
                    in_main_menu = False
            elif game_over:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    leaderboard.append((player_name, score))
                    ninja_y = GROUND_Y
                    jumping = False
                    jump_velocity = 0
                    jump_count = 0
                    stars.clear()
                    enemy_stars.clear()
                    obstacles.clear()
                    enemies.clear()
                    explosions.clear()
                    heart_powerups.clear()
                    score = 0
                    frame_count = 0
                    health = 3
                    game_over = False
                    paused = False
                elif event.key == pygame.K_m:
                    leaderboard.append((player_name, score))
                    score = 0
                    health = 3
                    game_over = False
                    paused = False
                    in_main_menu = True
                    show_name_input = True
                    input_text = ""
            elif not game_over:
                if event.key == pygame.K_f and star_cooldown == 0:
                    fire_star()
                    star_cooldown = 0
                elif event.key == pygame.K_p:
                    paused = not paused
                elif event.key == pygame.K_b and bomb_count > 0:
                    thrown_bombs.append([ninja_x + 40, ninja_y + 20])
                    bomb_count -= 1

    if in_main_menu:
        show_main_menu()

    elif not game_over and not paused:
        # Game logic & drawing...
        pass

    elif game_over:
        # Draw game over screen & handle logic
        show_game_over()



    if in_main_menu:
        show_main_menu()

    elif not game_over and not paused:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE] and not space_held:
            if jump_count < 2:
                jump_velocity = -17
                jumping = True
            space_held = True
        elif not keys[pygame.K_SPACE]:
            space_held = False
        draw_bomb_collectibles()
        draw_thrown_bombs()


        if jumping:
            ninja_y += jump_velocity
            jump_velocity += 1
            if ninja_y >= GROUND_Y:
                ninja_y = GROUND_Y
                jumping = False
                jump_count = 0

        draw_obstacles()
        draw_enemies()
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
        bomb_text = font.render(f"Bombs: {bomb_count}", True, (255, 255, 0))
        screen.blit(bomb_text, (10, 70))


        frame_count += 7
        if star_cooldown > 0:
            star_cooldown -= 1

    elif game_over:
        draw_obstacles()
        draw_enemies()
        draw_stars()
        draw_enemy_stars()
        draw_ninja()
        draw_explosions()
        draw_heart_powerups()
        draw_hearts()
        show_game_over()
        draw_bomb_collectibles()
        draw_thrown_bombs()


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
            enemies.clear()
            explosions.clear()
            heart_powerups.clear()
            score = 0
            frame_count = 0
            health = 3
            game_over = False
            paused = False


    pygame.display.flip()
    clock.tick(30)

















