"""Tank movement, shooting, collisions, and drawing; no external assets needed."""

from dataclasses import dataclass
import math
import random

import pygame

WIDTH, HEIGHT = 1100, 760
ARENA = pygame.Rect(28, 88, 1044, 560)
TANK_RADIUS = 20
TANK_SPEED = 220
BULLET_SPEED = 700
BULLET_RADIUS = 4
TARGET_RADIUS = 22
TARGET_GOAL = 10
FIRE_INTERVAL = 0.18

BG = (12, 21, 30)
FLOOR = (23, 39, 47)
LINE = (39, 61, 67)
TEXT = (230, 240, 232)
MUTED = (139, 162, 163)
GREEN = (128, 222, 151)
GOLD = (247, 197, 101)
RED = (232, 119, 103)


@dataclass
class Bullet:
    position: pygame.Vector2
    velocity: pygame.Vector2
    remaining: float = 1.6


@dataclass
class Target:
    position: pygame.Vector2
    health: int = 2
    flash: float = 0.0


@dataclass
class Particle:
    position: pygame.Vector2
    velocity: pygame.Vector2
    remaining: float
    color: tuple[int, int, int]


def circle_hits_rect(position: pygame.Vector2, radius: float, rect: pygame.Rect) -> bool:
    nearest = pygame.Vector2(max(rect.left, min(position.x, rect.right)),
                             max(rect.top, min(position.y, rect.bottom)))
    return position.distance_squared_to(nearest) < radius * radius


def segment_circle_hit(start: pygame.Vector2, end: pygame.Vector2,
                       center: pygame.Vector2, radius: float) -> float | None:
    """Return the first hit's fraction along a bullet's path (avoids tunneling)."""
    delta = end - start
    offset = start - center
    c = offset.length_squared() - radius * radius
    if c <= 0:
        return 0.0
    a = delta.length_squared()
    if a == 0:
        return None
    b = 2 * offset.dot(delta)
    discriminant = b * b - 4 * a * c
    if discriminant < 0:
        return None
    t = (-b - math.sqrt(discriminant)) / (2 * a)
    return t if 0 <= t <= 1 else None


def segment_rect_hit(start: pygame.Vector2, end: pygame.Vector2,
                     rect: pygame.Rect) -> float | None:
    """Intersect a segment with a rectangle using floating-point coordinates."""
    low, high = 0.0, 1.0
    delta = end - start
    for origin, direction, minimum, maximum in (
        (start.x, delta.x, rect.left, rect.right),
        (start.y, delta.y, rect.top, rect.bottom),
    ):
        if abs(direction) < 1e-9:
            if origin < minimum or origin > maximum:
                return None
            continue
        near, far = sorted(((minimum - origin) / direction,
                            (maximum - origin) / direction))
        low, high = max(low, near), min(high, far)
        if low > high:
            return None
    return low


class Game:
    def __init__(self, seed: int | None = None):
        self.random = random.Random(seed)
        self.font_small = pygame.font.Font(None, 21)
        self.font = pygame.font.Font(None, 27)
        self.font_title = pygame.font.Font(None, 42)
        self.font_big = pygame.font.Font(None, 68)
        self.running = True
        self.reset()

    def reset(self) -> None:
        self.tank_pos = pygame.Vector2(170, 368)
        self.hull_angle = 0.0
        self.turret_angle = 0.0
        self.mouse_pos = pygame.Vector2(700, 368)
        self.bullets: list[Bullet] = []
        self.particles: list[Particle] = []
        self.targets: list[Target] = []
        self.obstacles = [pygame.Rect(316, 170, 66, 140),
                          pygame.Rect(316, 426, 66, 140),
                          pygame.Rect(600, 294, 110, 66),
                          pygame.Rect(794, 470, 130, 50)]
        self.score = 0
        self.shots_fired = 0
        self.hits = 0
        self.elapsed = 0.0
        self.fire_cooldown = 0.0
        self.muzzle_flash = 0.0
        self.won = False
        for position in [(500, 185), (860, 190), (540, 487), (950, 355), (710, 568)]:
            self.targets.append(Target(pygame.Vector2(position)))

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.running = False
            elif event.key == pygame.K_r:
                self.reset()

    def _blocked(self, position: pygame.Vector2) -> bool:
        if any(circle_hits_rect(position, TANK_RADIUS, wall) for wall in self.obstacles):
            return True
        return any(position.distance_squared_to(target.position) <
                   (TANK_RADIUS + TARGET_RADIUS) ** 2 for target in self.targets)

    def _move(self, direction: pygame.Vector2, dt: float) -> None:
        if direction.length_squared() == 0:
            return
        direction = direction.normalize()
        self.hull_angle = math.degrees(math.atan2(direction.y, direction.x))
        displacement = direction * TANK_SPEED * dt
        # Small steps and separate axes let the tank slide along walls safely.
        steps = max(1, math.ceil(displacement.length() / 4))
        for _ in range(steps):
            for axis in (0, 1):
                candidate = self.tank_pos.copy()
                candidate[axis] += displacement[axis] / steps
                candidate.x = max(ARENA.left + TANK_RADIUS,
                                  min(candidate.x, ARENA.right - TANK_RADIUS))
                candidate.y = max(ARENA.top + TANK_RADIUS,
                                  min(candidate.y, ARENA.bottom - TANK_RADIUS))
                if not self._blocked(candidate):
                    self.tank_pos = candidate

    def _spawn_target(self) -> None:
        # Limit attempts so even a crowded arena can never freeze the game.
        for _ in range(250):
            pos = pygame.Vector2(self.random.randint(440, ARENA.right - 50),
                                 self.random.randint(ARENA.top + 50, ARENA.bottom - 50))
            if pos.distance_to(self.tank_pos) < 110:
                continue
            if any(circle_hits_rect(pos, TARGET_RADIUS + 18, wall) for wall in self.obstacles):
                continue
            if any(pos.distance_to(target.position) < 88 for target in self.targets):
                continue
            self.targets.append(Target(pos))
            return

    def _burst(self, position: pygame.Vector2, color: tuple[int, int, int], count: int) -> None:
        for _ in range(count):
            velocity = pygame.Vector2(self.random.uniform(35, 145), 0)
            velocity.rotate_ip(self.random.uniform(0, 360))
            self.particles.append(Particle(position.copy(), velocity,
                                           self.random.uniform(0.15, 0.45), color))

    def _update_bullets(self, dt: float) -> None:
        surviving = []
        for bullet in self.bullets:
            start = bullet.position
            end = start + bullet.velocity * dt
            first_t = 2.0
            hit_target = None
            for wall in self.obstacles:
                hit = segment_rect_hit(start, end, wall.inflate(BULLET_RADIUS * 2, BULLET_RADIUS * 2))
                if hit is not None and hit < first_t:
                    first_t = hit
            for target in self.targets:
                hit = segment_circle_hit(start, end, target.position, TARGET_RADIUS + BULLET_RADIUS)
                if hit is not None and hit < first_t:
                    first_t, hit_target = hit, target
            if first_t <= 1:
                position = start.lerp(end, first_t)
                self._burst(position, GOLD if hit_target else MUTED, 7)
                if hit_target:
                    self.hits += 1
                    hit_target.health -= 1
                    hit_target.flash = 0.12
                    if hit_target.health <= 0:
                        self._burst(hit_target.position, RED, 22)
                        self.targets.remove(hit_target)
                        self.score += 1
                        if self.score >= TARGET_GOAL:
                            self.won = True
                            self.bullets.clear()
                            return
                        if self.score + len(self.targets) < TARGET_GOAL:
                            self._spawn_target()
                continue
            bullet.position = end
            bullet.remaining -= dt
            if bullet.remaining > 0 and ARENA.collidepoint(end):
                surviving.append(bullet)
        self.bullets = surviving

    def update(self, dt: float, movement: tuple[float, float],
               mouse_pos: tuple[float, float], firing: bool) -> None:
        dt = max(0.0, min(dt, 0.05))
        self.mouse_pos = pygame.Vector2(mouse_pos)
        self.muzzle_flash = max(0.0, self.muzzle_flash - dt)
        for particle in self.particles:
            particle.position += particle.velocity * dt
            particle.remaining -= dt
        self.particles = [p for p in self.particles if p.remaining > 0]
        for target in self.targets:
            target.flash = max(0.0, target.flash - dt)
        if self.won:
            return
        self.elapsed += dt
        self.fire_cooldown = max(0.0, self.fire_cooldown - dt)
        self._move(pygame.Vector2(movement), dt)
        aim = self.mouse_pos - self.tank_pos
        if aim.length_squared() > 0:
            self.turret_angle = math.degrees(math.atan2(aim.y, aim.x))
        if firing and self.fire_cooldown <= 0:
            direction = pygame.Vector2(1, 0).rotate(self.turret_angle)
            # Starting inside the hull prevents firing through an adjacent wall.
            self.bullets.append(Bullet(self.tank_pos.copy(), direction * BULLET_SPEED))
            self.fire_cooldown = FIRE_INTERVAL
            self.muzzle_flash = 0.07
            self.shots_fired += 1
        self._update_bullets(dt)

    def _text(self, surface, text, position, color=TEXT, font=None) -> None:
        surface.blit((font or self.font).render(text, True, color), position)

    def _draw_target(self, surface, target: Target) -> None:
        p = target.position
        pygame.draw.circle(surface, (13, 27, 32), (int(p.x + 3), int(p.y + 6)), 29)
        pygame.draw.circle(surface, (73, 68, 62), p, 28, 1)
        pygame.draw.circle(surface, (56, 49, 47), p, 23)
        color = TEXT if target.flash > 0 else RED
        pygame.draw.circle(surface, color, p, 20, 3)
        pygame.draw.circle(surface, color, p, 11, 2)
        pygame.draw.circle(surface, color, p, 4)
        for dx in (-7, 3):
            pygame.draw.rect(surface, GREEN if (dx == -7 or target.health == 2) else LINE,
                             (p.x + dx, p.y + 32, 6, 4), border_radius=1)

    def _draw_tank(self, surface) -> None:
        hull = pygame.Surface((76, 70), pygame.SRCALPHA)
        for y in (9, 47):
            pygame.draw.rect(hull, (9, 22, 27), (9, y, 55, 14), border_radius=4)
            for x in range(14, 63, 8):
                pygame.draw.line(hull, (64, 88, 81), (x, y + 2), (x, y + 11), 3)
        pygame.draw.polygon(hull, (52, 94, 74), [(12, 25), (22, 17), (58, 17),
                                                               (66, 26), (66, 44), (58, 53), (22, 53), (12, 45)])
        pygame.draw.polygon(hull, GREEN, [(12, 25), (22, 17), (58, 17),
                                                    (66, 26), (66, 44), (58, 53), (22, 53), (12, 45)], 2)
        pygame.draw.line(hull, (100, 140, 102), (25, 23), (25, 47), 3)
        for y in (23, 44):
            pygame.draw.rect(hull, GOLD, (57, y, 5, 4), border_radius=1)
        rotated = pygame.transform.rotate(hull, -self.hull_angle)
        pygame.draw.circle(surface, (11, 29, 33), self.tank_pos + (3, 6), 30)
        surface.blit(rotated, rotated.get_rect(center=self.tank_pos))
        direction = pygame.Vector2(1, 0).rotate(self.turret_angle)
        muzzle = self.tank_pos + direction * 37
        pygame.draw.line(surface, (11, 27, 31), self.tank_pos, muzzle, 13)
        pygame.draw.line(surface, (171, 204, 149), self.tank_pos, muzzle, 7)
        pygame.draw.circle(surface, (38, 71, 61), self.tank_pos, 16)
        pygame.draw.circle(surface, GREEN, self.tank_pos, 16, 2)
        pygame.draw.circle(surface, (149, 188, 132), self.tank_pos, 7)
        pygame.draw.line(surface, GREEN, self.tank_pos, self.tank_pos + direction * 13, 3)
        if self.muzzle_flash:
            perpendicular = direction.rotate(90)
            pygame.draw.polygon(surface, GOLD, [muzzle + direction * 13,
                                                muzzle + perpendicular * 6,
                                                muzzle - direction * 3,
                                                muzzle - perpendicular * 6])

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(BG)
        self._text(surface, "IRON RANGE", (28, 23), font=self.font_title)
        self._text(surface, "TANK TRAINING / 01", (266, 35), MUTED, self.font_small)
        pygame.draw.circle(surface, GREEN, (782, 40), 4)
        self._text(surface, "RANGE ACTIVE" if not self.won else "COMPLETE", (795, 32), GREEN, self.font_small)
        self._text(surface, f"{int(self.elapsed) // 60:02}:{int(self.elapsed) % 60:02}", (1000, 28), GOLD)
        pygame.draw.rect(surface, FLOOR, ARENA, border_radius=10)
        surface.set_clip(ARENA)
        for x in range(ARENA.left, ARENA.right, 40):
            pygame.draw.line(surface, (28, 46, 53), (x, ARENA.top), (x, ARENA.bottom))
        for y in range(ARENA.top, ARENA.bottom, 40):
            pygame.draw.line(surface, (28, 46, 53), (ARENA.left, y), (ARENA.right, y))
        pygame.draw.circle(surface, (33, 55, 59), (170, 368), 70, 1)
        pygame.draw.circle(surface, (33, 55, 59), (170, 368), 77, 1)
        self._text(surface, "DEPLOY", (144, 451), (66, 92, 94), self.font_small)
        self._text(surface, "DESTROY 10 TARGETS  /  2 HITS EACH", (49, 106), MUTED, self.font_small)
        for wall in self.obstacles:
            pygame.draw.rect(surface, (12, 27, 32), wall.move(5, 6), border_radius=5)
            pygame.draw.rect(surface, (55, 73, 76), wall, border_radius=4)
            pygame.draw.rect(surface, (85, 103, 100), wall, 2, border_radius=4)
            pygame.draw.line(surface, (123, 136, 116), (wall.left + 5, wall.top + 4),
                             (wall.right - 5, wall.top + 4), 2)
            for x in range(wall.left + 10, wall.right - 4, 14):
                pygame.draw.line(surface, GOLD, (x, wall.bottom - 8), (x + 5, wall.bottom - 8), 3)
        for target in self.targets:
            self._draw_target(surface, target)
        for bullet in self.bullets:
            tail = bullet.position - bullet.velocity.normalize() * 13 if bullet.velocity.length_squared() else bullet.position
            pygame.draw.line(surface, (145, 128, 77), tail, bullet.position, 3)
            pygame.draw.circle(surface, GOLD, bullet.position, BULLET_RADIUS)
            pygame.draw.circle(surface, TEXT, bullet.position, 2)
        for particle in self.particles:
            pygame.draw.circle(surface, particle.color, particle.position, max(1, int(particle.remaining * 8)))
        self._draw_tank(surface)
        if ARENA.collidepoint(self.mouse_pos) and not self.won:
            color = RED if any(self.mouse_pos.distance_to(t.position) < TARGET_RADIUS for t in self.targets) else GOLD
            pygame.draw.circle(surface, color, self.mouse_pos, 12, 1)
            for direction in (pygame.Vector2(1, 0), pygame.Vector2(0, 1)):
                for sign in (-1, 1):
                    pygame.draw.line(surface, color, self.mouse_pos + direction * 17 * sign,
                                     self.mouse_pos + direction * 8 * sign, 2)
            pygame.draw.circle(surface, TEXT, self.mouse_pos, 2)
        surface.set_clip(None)
        pygame.draw.rect(surface, (65, 89, 89), ARENA, 2, border_radius=10)
        self._text(surface, "TARGETS DESTROYED", (30, 670), MUTED, self.font_small)
        self._text(surface, f"{self.score:02} / {TARGET_GOAL}", (30, 694), GOLD, self.font_title)
        for i in range(TARGET_GOAL):
            pygame.draw.rect(surface, GREEN if i < self.score else LINE,
                             (177 + i * 13, 704, 8, 20), border_radius=2)
        for x, heading, caption in [(350, "W A S D", "MOVE"), (506, "MOUSE", "AIM"),
                                     (651, "LEFT CLICK", "FIRE / HOLD"), (840, "R", "RESTART"),
                                     (976, "ESC", "EXIT")]:
            self._text(surface, heading, (x, 672))
            self._text(surface, caption, (x, 707), MUTED, self.font_small)
        if self.won:
            shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            shade.fill((5, 14, 20, 190))
            surface.blit(shade, (0, 0))
            panel = pygame.Rect(285, 250, 530, 245)
            pygame.draw.rect(surface, BG, panel, border_radius=14)
            pygame.draw.rect(surface, GREEN, panel, 2, border_radius=14)
            for text, y, font, color in [
                ("TRAINING COMPLETE", 278, self.font_small, GREEN),
                ("RANGE CLEARED", 314, self.font_big, TEXT),
                (f"10 targets  /  {self.shots_fired} shots  /  {self.elapsed:.1f}s", 385, self.font, GOLD),
                ("Press R to play again  |  ESC to exit", 443, self.font, MUTED),
            ]:
                rendered = font.render(text, True, color)
                surface.blit(rendered, rendered.get_rect(midtop=(WIDTH // 2, y)))
