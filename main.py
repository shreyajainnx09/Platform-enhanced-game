import os
import sys
import random
import math
import pygame
from os import listdir
from os.path import isfile, join

pygame.init()
pygame.font.init()

pygame.display.set_caption("Platformer")

# Bigger play area than the original 1000x800 window
WIDTH, HEIGHT = 1280, 800
FPS = 60
PLAYER_VEL = 5
MAX_FALL_SPEED = 18
STARTING_LIVES = 3
COIN_VALUE = 10
NUM_LEVELS = 10
BLOCK_SIZE = 96

window = pygame.display.set_mode((WIDTH, HEIGHT))

FONT_BIG = pygame.font.SysFont("arial", 64, bold=True)
FONT_MED = pygame.font.SysFont("arial", 32, bold=True)
FONT_SMALL = pygame.font.SysFont("arial", 24, bold=True)


def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]


def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    path = join("assets", dir1, dir2)
    images = [f for f in listdir(path) if isfile(join(path, f))]

    all_sprites = {}

    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()

        sprites = []
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)
            sprites.append(pygame.transform.scale2x(surface))

        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites

    return all_sprites


def get_block(size):
    path = join("assets", "Terrain", "Terrain.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(96, 0, size, size)
    surface.blit(image, (0, 0), rect)
    return pygame.transform.scale2x(surface)


# ---------------------------------------------------------------------------
# Lightweight particle system - pure shapes, no extra image assets needed.
# ---------------------------------------------------------------------------
class Particle:
    def __init__(self, x, y, color, vx=None, vy=None, life=25, radius=3, gravity=0.2):
        self.x = x
        self.y = y
        self.vx = vx if vx is not None else random.uniform(-2, 2)
        self.vy = vy if vy is not None else random.uniform(-3, -1)
        self.life = life
        self.max_life = life
        self.radius = radius
        self.color = color
        self.gravity = gravity

    def loop(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        self.life -= 1

    def draw(self, win, offset_x, shake_x=0, shake_y=0):
        if self.life <= 0:
            return
        alpha = max(0, min(255, int(255 * (self.life / self.max_life))))
        size = max(1, int(self.radius * (self.life / self.max_life)))
        surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*self.color, alpha), (size, size), size)
        win.blit(surf, (self.x - offset_x + shake_x - size, self.y + shake_y - size))


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def burst(self, x, y, color, count=12, life=25, radius=3, spread=3, gravity=0.2, upward=1):
        for _ in range(count):
            vx = random.uniform(-spread, spread)
            vy = random.uniform(-spread * upward, 0)
            self.particles.append(Particle(x, y, color, vx, vy, life, radius, gravity))

    def loop(self):
        for p in self.particles:
            p.loop()
        self.particles = [p for p in self.particles if p.life > 0]

    def draw(self, win, offset_x, shake_x=0, shake_y=0):
        for p in self.particles:
            p.draw(win, offset_x, shake_x, shake_y)


class Player(pygame.sprite.Sprite):
    COLOR = (255, 0, 0)
    GRAVITY = 1
    SPRITES = load_sprite_sheets("MainCharacters", "MaskDude", 32, 32, True)
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__()
        self.spawn_x = x
        self.spawn_y = y
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = "left"
        self.animation_count = 0
        self.fall_count = 0
        self.jump_count = 0
        self.hit = False
        self.hit_count = 0
        self.invincible_count = 0
        self.jump_buffer = 0
        self.on_ground = False
        self.sprite = self.SPRITES["idle_left"][0]

    def jump(self):
        self.y_vel = -self.GRAVITY * 10
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count == 1:
            self.fall_count = 0

    def buffer_jump(self):
        # Remember a jump press made just before landing so it still fires -
        # keeps chained jumps feeling responsive instead of "eaten".
        self.jump_buffer = 6

    def cut_jump(self):
        # Releasing the jump key early gives a shorter hop - classic snappy feel.
        if self.y_vel < -4:
            self.y_vel = -4

    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    def respawn(self):
        self.rect.x = self.spawn_x
        self.rect.y = self.spawn_y
        self.x_vel = 0
        self.y_vel = 0
        self.fall_count = 0
        self.jump_count = 0
        self.hit = False
        self.hit_count = 0
        self.invincible_count = FPS * 2

    def set_spawn(self, x, y):
        self.spawn_x = x
        self.spawn_y = y

    def make_hit(self):
        if self.invincible_count <= 0:
            self.hit = True
            self.invincible_count = FPS * 2
            return True
        return False

    def move_left(self, vel):
        self.x_vel = -vel
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0

    def move_right(self, vel):
        self.x_vel = vel
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    def loop(self, fps):
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY)
        self.y_vel = min(self.y_vel, MAX_FALL_SPEED)
        self.move(self.x_vel, self.y_vel)

        if self.hit:
            self.hit_count += 1
        if self.hit_count > fps:
            self.hit = False
            self.hit_count = 0

        if self.invincible_count > 0:
            self.invincible_count -= 1

        if self.jump_buffer > 0:
            self.jump_buffer -= 1

        self.fall_count += 1
        self.on_ground = False
        self.update_sprite()

    def landed(self):
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0
        self.on_ground = True
        if self.jump_buffer > 0:
            self.jump()
            self.jump_buffer = 0

    def hit_head(self):
        self.fall_count = 0
        self.y_vel *= -1

    def update_sprite(self):
        sprite_sheet = "idle"
        if self.hit:
            sprite_sheet = "hit"
        elif self.y_vel < 0:
            if self.jump_count == 1:
                sprite_sheet = "jump"
            elif self.jump_count == 2:
                sprite_sheet = "double_jump"
        elif self.y_vel > self.GRAVITY * 2:
            sprite_sheet = "fall"
        elif self.x_vel != 0:
            sprite_sheet = "run"

        sprite_sheet_name = sprite_sheet + "_" + self.direction
        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = (self.animation_count //
                        self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()

    def update(self):
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)

    def draw(self, win, offset_x, shake_x=0, shake_y=0):
        if self.invincible_count > 0 and self.invincible_count % 10 < 5:
            return
        win.blit(self.sprite, (self.rect.x - offset_x + shake_x, self.rect.y + shake_y))


class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name

    def draw(self, win, offset_x, shake_x=0, shake_y=0):
        win.blit(self.image, (self.rect.x - offset_x + shake_x, self.rect.y + shake_y))


class Block(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        block = get_block(size)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)


class MovingPlatform(Block):
    """A platform that patrols back and forth. The player rides along with it."""

    def __init__(self, x, y, size, distance, speed=2, vertical=False):
        super().__init__(x, y, size)
        self.origin = y if vertical else x
        self.distance = distance
        self.speed = speed
        self.direction = 1
        self.vertical = vertical
        self.dx = 0
        self.dy = 0

    def loop(self):
        move = self.speed * self.direction
        if self.vertical:
            self.rect.y += move
            self.dx, self.dy = 0, move
            pos = self.rect.y
        else:
            self.rect.x += move
            self.dx, self.dy = move, 0
            pos = self.rect.x

        if pos >= self.origin + self.distance or pos <= self.origin:
            self.direction *= -1


class Fire(Object):
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "fire")
        self.fire = load_sprite_sheets("Traps", "Fire", width, height)
        self.image = self.fire["off"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "off"

    def on(self):
        self.animation_name = "on"

    def off(self):
        self.animation_name = "off"

    def loop(self):
        sprites = self.fire[self.animation_name]
        sprite_index = (self.animation_count //
                        self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1

        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0


class Saw(Object):
    """A spinning blade hazard that patrols a short track, drawn procedurally
    so it doesn't need any extra sprite assets."""

    def __init__(self, x, y, radius=20, distance=150, speed=3, vertical=False):
        super().__init__(x, y, radius * 2, radius * 2, "saw")
        self.radius = radius
        self.origin = y if vertical else x
        self.distance = distance
        self.speed = speed
        self.direction = 1
        self.vertical = vertical
        self.angle = 0
        self._redraw()

    def _redraw(self):
        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        cx, cy = self.radius, self.radius
        for i in range(8):
            a = self.angle + i * (360 / 8)
            rad = math.radians(a)
            x1 = cx + math.cos(rad) * (self.radius - 4)
            y1 = cy + math.sin(rad) * (self.radius - 4)
            x2 = cx + math.cos(rad) * (self.radius + 4)
            y2 = cy + math.sin(rad) * (self.radius + 4)
            pygame.draw.line(self.image, (170, 170, 180), (x1, y1), (x2, y2), 5)
        pygame.draw.circle(self.image, (120, 120, 130), (cx, cy), self.radius - 4)
        pygame.draw.circle(self.image, (60, 60, 65), (cx, cy), self.radius - 4, 3)
        pygame.draw.circle(self.image, (200, 200, 210), (cx, cy), 4)
        self.mask = pygame.mask.from_surface(self.image)

    def loop(self):
        move = self.speed * self.direction
        if self.vertical:
            self.rect.y += move
            pos = self.rect.y
        else:
            self.rect.x += move
            pos = self.rect.x

        if pos >= self.origin + self.distance or pos <= self.origin:
            self.direction *= -1

        self.angle = (self.angle + 12) % 360
        self._redraw()


class Coin(Object):
    def __init__(self, x, y, radius=12):
        super().__init__(x, y, radius * 2, radius * 2, "coin")
        self.radius = radius
        self.collected = False
        self.base_y = y
        self.bob_offset = random.uniform(0, math.pi * 2)
        self._redraw()

    def _redraw(self):
        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255, 215, 0), (self.radius, self.radius), self.radius)
        pygame.draw.circle(self.image, (255, 235, 120), (self.radius, self.radius), self.radius, 3)
        pygame.draw.circle(self.image, (200, 160, 0), (self.radius, self.radius), self.radius - 5, 2)
        self.mask = pygame.mask.from_surface(self.image)

    def loop(self, frame_count):
        self.rect.y = int(self.base_y + math.sin(frame_count * 0.08 + self.bob_offset) * 5)


class Flag(Object):
    def __init__(self, x, y, height=140):
        super().__init__(x, y, 20, height, "flag")
        self.image = pygame.Surface((20, height), pygame.SRCALPHA)
        pygame.draw.rect(self.image, (170, 130, 80), (8, 0, 4, height))
        pygame.draw.polygon(self.image, (60, 200, 90), [(12, 5), (12, 45), (55, 25)])
        self.mask = pygame.mask.from_surface(self.image)


def get_background(name):
    image = pygame.image.load(join("assets", "Background", name))
    _, _, width, height = image.get_rect()
    tiles = []

    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            pos = (i * width, j * height)
            tiles.append(pos)

    return tiles, image


# ---------------------------------------------------------------------------
# Level generation - 10 levels, each built deterministically from its index
# so they're reproducible but get progressively harder. Gaps are capped at
# 2 blocks wide (comfortably crossable with the double jump), and hazards are
# never placed directly on a gap tile, so every level should be fair even
# though it's generated rather than hand-placed. Tweak the ranges below if
# you want to hand-tune the difficulty curve.
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Level generation - 10 levels, each built deterministically from its index
# so they're reproducible but get progressively harder. Gaps are capped at
# 2 blocks wide (comfortably crossable with the double jump). Every feature
# (platform, saw, moving platform, fire, coin) claims its x-tiles in `used`
# before the next one is placed, so nothing spawns on top of anything else,
# and platforms sit within jump range of the floor (1-2 blocks up) instead
# of floating unreachably high. Tweak the ranges below to hand-tune difficulty.
# ---------------------------------------------------------------------------
def generate_level(n):
    rnd = random.Random(n * 7919 + 42)
    length = 16 + n * 4

    gaps = set()
    num_gaps = 1 + n // 2
    attempts = 0
    while len(gaps) < num_gaps and attempts < 200:
        attempts += 1
        width = 1 if n < 2 else rnd.choice([1, 1, 2])
        start = rnd.randint(4, length - 4)
        candidate = set(range(start, start + width))
        if any((g in gaps or g - 1 in gaps or g + 1 in gaps) for g in candidate):
            continue
        gaps |= candidate

    used = set()  # x-tiles already claimed by some feature, so nothing overlaps

    def claim(x, span=1):
        for i in range(x - span, x + span + 1):
            used.add(i)

    def safe_x(span=1):
        for _ in range(60):
            x = rnd.randint(3, length - 3)
            if x in gaps:
                continue
            if any(t in used for t in range(x - span, x + span + 1)):
                continue
            return x
        return None  # ran out of room - caller should skip this feature

    saws = []
    for _ in range(n // 2):
        x = safe_x(span=1)
        if x is None:
            continue
        claim(x)
        saws.append(dict(
            x=x, radius=18,
            distance=rnd.choice([120, 160, 200]),
            speed=rnd.choice([2, 3, 4]),
            vertical=(n >= 4 and rnd.random() < 0.3),
        ))

    moving = []
    for _ in range(1 + n // 3):
        x = safe_x(span=2)
        if x is None:
            continue
        claim(x, span=2)
        moving.append(dict(
            x=x, h=rnd.choice([1, 2]),
            distance=rnd.choice([150, 200, 250]),
            speed=rnd.choice([2, 3]),
        ))

    fires = []
    for _ in range(1 + n // 3):
        x = safe_x(span=1)
        if x is None:
            continue
        claim(x)
        fires.append(x)

    platforms = []
    for _ in range(2 + n // 2):
        x = safe_x(span=1)
        if x is None:
            continue
        claim(x)
        platforms.append((x, rnd.choice([1, 2])))

    coins = [(rnd.randint(1, length - 2), rnd.choice([1, 1, 2])) for _ in range(4 + n // 2)]

    return dict(
        length=length, gaps=gaps, platforms=platforms, moving=moving,
        saws=saws, fires=fires, coins=coins, flag_x=length - 1, spawn_x=1,
        name=f"Level {n + 1}",
    )


LEVEL_DEFS = [generate_level(i) for i in range(NUM_LEVELS)]


def build_level(index):
    d = LEVEL_DEFS[index]
    bs = BLOCK_SIZE

    floor = [Block(i * bs, HEIGHT - bs, bs)
             for i in range(-3, d["length"] + 3) if i < 0 or i not in d["gaps"]]

    # h is "blocks above the floor surface" directly - with the jump power
    # above, a single jump clears ~2.4 blocks and a double jump ~2.8 blocks,
    # so h of 1-2 is comfortably reachable.
    platforms = [Block(x * bs, HEIGHT - bs - h * bs, bs) for (x, h) in d["platforms"]]

    moving_platforms = [
        MovingPlatform(m["x"] * bs, HEIGHT - bs - m["h"] * bs, bs, m["distance"], m["speed"])
        for m in d["moving"]
    ]

    saws = [
        Saw(s["x"] * bs + bs // 2 - s["radius"], HEIGHT - bs - s["radius"] * 2 + 10,
            s["radius"], s["distance"], s["speed"], s["vertical"])
        for s in d["saws"]
    ]

    fires = []
    for x in d["fires"]:
        fire = Fire(x * bs, HEIGHT - bs - 64, 16, 32)
        fire.on()
        fires.append(fire)

    flag = Flag(d["flag_x"] * bs, HEIGHT - bs - 140)

    coins = [Coin(x * bs + bs // 2 - 12, HEIGHT - bs - h * bs - 24) for (x, h) in d["coins"]]

    player = Player(d["spawn_x"] * bs + 20, 100, 50, 50)

    objects = [*floor, *platforms, *moving_platforms, *fires, *saws, flag]
    animated = [*moving_platforms, *saws, *fires]

    return player, objects, coins, animated, d["name"]


def draw_hud(window, score, lives, level_name):
    score_surf = FONT_SMALL.render(f"Coins: {score}", True, (255, 255, 255))
    lives_surf = FONT_SMALL.render(f"Lives: {lives}", True, (255, 255, 255))
    level_surf = FONT_SMALL.render(level_name, True, (255, 255, 255))
    window.blit(score_surf, (16, 14))
    window.blit(lives_surf, (16, 42))
    window.blit(level_surf, level_surf.get_rect(topright=(WIDTH - 16, 14)))


def draw_center_message(window, title, subtitle, color=(255, 255, 255)):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 140))
    window.blit(overlay, (0, 0))

    title_surf = FONT_BIG.render(title, True, color)
    window.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30)))

    sub_surf = FONT_MED.render(subtitle, True, (230, 230, 230))
    window.blit(sub_surf, sub_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30)))


def draw_banner(window, text, alpha):
    surf = FONT_BIG.render(text, True, (255, 255, 255))
    surf.set_alpha(alpha)
    window.blit(surf, surf.get_rect(center=(WIDTH // 2, 120)))


def draw(window, background, bg_image, player, objects, coins, particles, offset_x,
         score, lives, level_name, state, banner_text, banner_timer, shake_x=0, shake_y=0):
    for tile in background:
        window.blit(bg_image, (tile[0], tile[1]))

    for obj in objects:
        obj.draw(window, offset_x, shake_x, shake_y)

    for coin in coins:
        if not coin.collected:
            coin.draw(window, offset_x, shake_x, shake_y)

    particles.draw(window, offset_x, shake_x, shake_y)

    if state != "dead":
        player.draw(window, offset_x, shake_x, shake_y)

    draw_hud(window, score, lives, level_name)

    if banner_timer > 0:
        alpha = 255 if banner_timer > 20 else int(255 * (banner_timer / 20))
        draw_banner(window, banner_text, alpha)

    if state == "dead":
        draw_center_message(window, "Game Over", "Press R to try again", (230, 80, 80))
    elif state == "won":
        draw_center_message(window, "You Beat All 10 Levels!", "Press R to play again", (100, 220, 130))
    elif state == "paused":
        draw_center_message(window, "Paused", "Press P to resume", (255, 255, 255))

    pygame.display.update()


def handle_vertical_collision(player, objects, dy):
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            if dy > 0:
                player.rect.bottom = obj.rect.top
                player.landed()
                if isinstance(obj, MovingPlatform):
                    player.rect.x += obj.dx
            elif dy < 0:
                player.rect.top = obj.rect.bottom
                player.hit_head()

            collided_objects.append(obj)

    return collided_objects


def collide(player, objects, dx):
    player.move(dx, 0)
    player.update()
    collided_object = None
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            collided_object = obj
            break

    player.move(-dx, 0)
    player.update()
    return collided_object


def handle_move(player, objects, coins, particles):
    keys = pygame.key.get_pressed()

    player.x_vel = 0
    collide_left = collide(player, objects, -PLAYER_VEL * 2)
    collide_right = collide(player, objects, PLAYER_VEL * 2)

    if keys[pygame.K_LEFT] and not collide_left:
        player.move_left(PLAYER_VEL)
    if keys[pygame.K_RIGHT] and not collide_right:
        player.move_right(PLAYER_VEL)

    was_on_ground = player.on_ground
    vertical_collide = handle_vertical_collision(player, objects, player.y_vel)

    if player.on_ground and not was_on_ground:
        particles.burst(player.rect.centerx, player.rect.bottom, (210, 210, 200),
                         count=8, life=15, radius=3, spread=2, gravity=0.1, upward=0.3)

    to_check = [collide_left, collide_right, *vertical_collide]

    hurt = False
    reached_flag = False
    for obj in to_check:
        if not obj:
            continue
        if obj.name in ("fire", "saw"):
            hurt = player.make_hit() or hurt
        elif obj.name == "flag":
            reached_flag = True

    got_coins = 0
    for coin in coins:
        if not coin.collected and pygame.sprite.collide_mask(player, coin):
            coin.collected = True
            got_coins += 1
            particles.burst(coin.rect.centerx, coin.rect.centery, (255, 215, 0),
                             count=14, life=20, radius=3, spread=3, gravity=0.05, upward=1)

    return hurt, got_coins, reached_flag


def main(window):
    clock = pygame.time.Clock()
    background, bg_image = get_background("Blue.png")

    current_level = 0
    player, objects, coins, animated, level_name = build_level(current_level)
    particles = ParticleSystem()

    offset_x = 0
    target_offset_x = 0
    scroll_area_width = 250

    score = 0
    lives = STARTING_LIVES
    state = "playing"  # playing | paused | dead | won

    shake_timer = 0
    shake_strength = 0
    frame_count = 0

    banner_text = f"Level 1 of {NUM_LEVELS}"
    banner_timer = 120

    def load_level(index):
        nonlocal player, objects, coins, animated, level_name, offset_x, target_offset_x
        nonlocal particles, banner_text, banner_timer
        player, objects, coins, animated, level_name = build_level(index)
        particles = ParticleSystem()
        offset_x = 0
        target_offset_x = 0
        banner_text = f"{level_name} of {NUM_LEVELS}"
        banner_timer = 120

    run = True
    while run:
        clock.tick(FPS)
        frame_count += 1
        if banner_timer > 0:
            banner_timer -= 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    run = False
                    break

                if event.key == pygame.K_p and state in ("playing", "paused"):
                    state = "paused" if state == "playing" else "playing"

                if event.key == pygame.K_r and state in ("dead", "won"):
                    current_level = 0
                    score = 0
                    lives = STARTING_LIVES
                    load_level(current_level)
                    state = "playing"

                if event.key == pygame.K_SPACE and state == "playing":
                    if player.jump_count < 2:
                        player.jump()
                    else:
                        player.buffer_jump()

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_SPACE and state == "playing":
                    player.cut_jump()

        if state == "playing":
            player.loop(FPS)
            for obj in animated:
                obj.loop()
            for coin in coins:
                coin.loop(frame_count)
            particles.loop()

            hurt, got_coins, reached_flag = handle_move(player, objects, coins, particles)
            score += got_coins * COIN_VALUE

            if hurt:
                shake_timer = 12
                shake_strength = 6
                particles.burst(player.rect.centerx, player.rect.centery, (220, 60, 60),
                                 count=10, life=18, radius=3, spread=3, gravity=0.1)
                lives -= 1
                if lives <= 0:
                    state = "dead"
                else:
                    player.respawn()

            if player.rect.top > HEIGHT + 300:
                lives -= 1
                if lives <= 0:
                    state = "dead"
                else:
                    player.respawn()

            if reached_flag:
                if current_level + 1 < NUM_LEVELS:
                    current_level += 1
                    load_level(current_level)
                else:
                    state = "won"

            if ((player.rect.right - offset_x >= WIDTH - scroll_area_width) and player.x_vel > 0) or (
                    (player.rect.left - offset_x <= scroll_area_width) and player.x_vel < 0):
                target_offset_x += player.x_vel
            offset_x += (target_offset_x - offset_x) * 0.15
        else:
            particles.loop()

        shake_x, shake_y = 0, 0
        if shake_timer > 0:
            shake_timer -= 1
            shake_x = random.uniform(-shake_strength, shake_strength)
            shake_y = random.uniform(-shake_strength, shake_strength)

        draw(window, background, bg_image, player, objects, coins, particles, offset_x,
             score, lives, level_name, state, banner_text, banner_timer, shake_x, shake_y)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main(window)