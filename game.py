import pygame
import random
import math
import sys

pygame.init()
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
win = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Speed Demon - Advanced Boss Mode")
clock = pygame.time.Clock()
FPS = 90

# Цвета
WHITE = (255, 255, 255)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
ORANGE = (255, 150, 0)
PLAYER_COLOR = (0, 255, 0)
BG_COLOR = (20, 20, 20)

# Игрок
player_size = 20
player_speed = 5
player = pygame.Rect(WIDTH // 2, HEIGHT - 100, player_size, player_size)

# Босс
boss_radius = 60
boss_pos = [WIDTH // 2, HEIGHT // 2]
boss_hp = 5

# Прицел
cursor_radius = 10

# Пули
bullet_speed = 6
bullets = []

# Орбы-клоны
clone_rings = []
last_clone_time = 0
clone_wave_index = 0
clone_wave_timer = 0
clone_active = False

# Настройки кольца
RING_DISTANCE = 250  # Увеличено расстояние от игрока
RING_SHOOT_DELAY = 0.5  # секунды
RING_WAVE_INTERVAL = 0.4
RING_COOLDOWN = 5
RING_MOVE_DELAY = 1  # Задержка перед движением орбов в секундах

# Спавн обычных пуль
def spawn_bullets():
    for angle in range(0, 360, 30):
        rad = math.radians(angle)
        dx = math.cos(rad) * bullet_speed
        dy = math.sin(rad) * bullet_speed
        bullets.append([boss_pos[0], boss_pos[1], dx, dy])
    # На игрока
    dx = player.centerx - boss_pos[0]
    dy = player.centery - boss_pos[1]
    dist = math.hypot(dx, dy)
    if dist != 0:
        dx, dy = dx / dist * bullet_speed, dy / dist * bullet_speed
        bullets.append([boss_pos[0], boss_pos[1], dx, dy])

# Спавн кольца
def spawn_clone_ring(pos):
    clones = []
    for angle in range(0, 360, 30):
        rad = math.radians(angle)
        x = pos[0] + math.cos(rad) * RING_DISTANCE
        y = pos[1] + math.sin(rad) * RING_DISTANCE
        clones.append({
            "x": x,
            "y": y,
            "target": pos,
            "fired": False,
            "timer": 0,
            "move_timer": 0  # Таймер для задержки перед движением
        })
    clone_rings.append(clones)

# Проверка на попадание по боссу
def is_cursor_on_boss(mouse_pos):
    dx = mouse_pos[0] - boss_pos[0]
    dy = mouse_pos[1] - boss_pos[1]
    return math.hypot(dx, dy) < boss_radius

# Основной цикл
running = True
spawn_timer = 0

while running:
    dt = clock.tick(FPS) / 1000  # секунд за кадр
    win.fill(BG_COLOR)
    mouse_pos = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if is_cursor_on_boss(mouse_pos):
                boss_hp -= 1
                print(f"Boss HP: {boss_hp}")
                if boss_hp <= 0:
                    print("Boss defeated!")
                    pygame.quit()
                    sys.exit()

    # Управление
    keys = pygame.key.get_pressed()
    if keys[pygame.K_w]: player.y -= player_speed
    if keys[pygame.K_s]: player.y += player_speed
    if keys[pygame.K_a]: player.x -= player_speed
    if keys[pygame.K_d]: player.x += player_speed
    player.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT))

    # Спавн обычных пуль
    spawn_timer += dt
    if spawn_timer >= 1.2:
        spawn_bullets()
        spawn_timer = 0

    # Обновление пуль
    for b in bullets:
        b[0] += b[2]
        b[1] += b[3]
    bullets = [b for b in bullets if 0 <= b[0] <= WIDTH and 0 <= b[1] <= HEIGHT]

    # Урон от пуль
    for b in bullets:
        if player.collidepoint(b[0], b[1]):
            print("YOU DIED")
            pygame.quit()
            sys.exit()

    # Кольцо орбов (3 волны)
    time_since_last = pygame.time.get_ticks() / 1000 - last_clone_time
    if time_since_last >= RING_COOLDOWN and not clone_active:
        clone_active = True
        clone_wave_index = 0
        clone_wave_timer = 0
        last_clone_time = pygame.time.get_ticks() / 1000

    if clone_active:
        clone_wave_timer += dt
        if clone_wave_index < 3 and clone_wave_timer >= clone_wave_index * RING_WAVE_INTERVAL:
            spawn_clone_ring(player.center)
            clone_wave_index += 1

        if clone_wave_index >= 3 and clone_wave_timer >= 3:
            clone_active = False
            clone_wave_timer = 0

    # Обновление орбов с задержкой
    for ring in clone_rings:
        for orb in ring:
            orb["timer"] += dt
            if orb["timer"] >= RING_SHOOT_DELAY:  # Задержка перед началом движения орба
                orb["move_timer"] += dt
                if orb["move_timer"] >= RING_MOVE_DELAY and not orb["fired"]:
                    dx = orb["target"][0] - orb["x"]
                    dy = orb["target"][1] - orb["y"]
                    dist = math.hypot(dx, dy)
                    if dist != 0:
                        orb["dx"] = dx / dist * (bullet_speed + 2)
                        orb["dy"] = dy / dist * (bullet_speed + 2)
                        orb["fired"] = True
            if orb.get("fired", False):
                orb["x"] += orb["dx"]
                orb["y"] += orb["dy"]

    # Урон от орбов
    for ring in clone_rings:
        for orb in ring:
            if player.collidepoint(orb["x"], orb["y"]) and orb.get("fired", False):
                print("YOU DIED")
                pygame.quit()
                sys.exit()

    # Удаление орбов за экраном
    for ring in clone_rings:
        ring[:] = [orb for orb in ring if 0 <= orb["x"] <= WIDTH and 0 <= orb["y"] <= HEIGHT]
    clone_rings[:] = [ring for ring in clone_rings if len(ring) > 0]

    # Рендер
    pygame.draw.circle(win, RED, boss_pos, boss_radius)
    pygame.draw.rect(win, PLAYER_COLOR, player)

    for b in bullets:
        pygame.draw.circle(win, ORANGE, (int(b[0]), int(b[1])), 5)

    for ring in clone_rings:
        for orb in ring:
            color = ORANGE if orb.get("fired", False) else YELLOW
            pygame.draw.circle(win, color, (int(orb["x"]), int(orb["y"])), 8)

    # Рендер прицела
    pygame.draw.circle(win, WHITE, mouse_pos, cursor_radius, 2)

    pygame.display.update()

pygame.quit()

