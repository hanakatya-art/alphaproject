"""Headless regression tests for controls, combat, and game lifecycle."""

import os
import unittest

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

import pygame

import tank_game


class TankGameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((tank_game.WIDTH, tank_game.HEIGHT))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.game = tank_game.Game(seed=42)
        self.game.targets.clear()
        self.game.obstacles.clear()
        self.game.tank_pos = pygame.Vector2(tank_game.ARENA.center)

    def advance(self, dt=0.05, movement=(0, 0), mouse=None, firing=False):
        if mouse is None:
            mouse = self.game.tank_pos + pygame.Vector2(100, 0)
        self.game.update(dt, movement, mouse, firing)

    def test_wasd_directions_move_at_expected_speed(self):
        center = pygame.Vector2(tank_game.ARENA.center)
        for movement in ((0, -1), (-1, 0), (0, 1), (1, 0)):
            with self.subTest(movement=movement):
                self.game.tank_pos = center.copy()
                self.advance(movement=movement)
                expected = center + pygame.Vector2(movement) * tank_game.TANK_SPEED * 0.05
                self.assertLess(self.game.tank_pos.distance_to(expected), 0.001)

    def test_diagonal_movement_is_not_faster(self):
        before = self.game.tank_pos.copy()
        self.advance(movement=(1, 1))
        self.assertAlmostEqual(
            self.game.tank_pos.distance_to(before), tank_game.TANK_SPEED * 0.05, places=5
        )

    def test_long_frame_is_capped(self):
        before = self.game.tank_pos.copy()
        self.advance(dt=5.0, movement=(1, 0))
        self.assertLessEqual(
            self.game.tank_pos.distance_to(before), tank_game.TANK_SPEED * 0.05 + 0.001
        )

    def test_tank_stays_inside_each_arena_edge(self):
        arena = tank_game.ARENA
        radius = tank_game.TANK_RADIUS
        cases = (
            ((arena.left + radius + 1, arena.centery), (-1, 0)),
            ((arena.right - radius - 1, arena.centery), (1, 0)),
            ((arena.centerx, arena.top + radius + 1), (0, -1)),
            ((arena.centerx, arena.bottom - radius - 1), (0, 1)),
        )
        for position, movement in cases:
            with self.subTest(movement=movement):
                self.game.tank_pos = pygame.Vector2(position)
                self.advance(movement=movement)
                self.assertGreaterEqual(self.game.tank_pos.x, arena.left + radius)
                self.assertLessEqual(self.game.tank_pos.x, arena.right - radius)
                self.assertGreaterEqual(self.game.tank_pos.y, arena.top + radius)
                self.assertLessEqual(self.game.tank_pos.y, arena.bottom - radius)

    def test_tank_slides_along_wall_without_crossing_it(self):
        before = self.game.tank_pos.copy()
        wall = pygame.Rect(before.x + tank_game.TANK_RADIUS + 2, before.y - 80, 20, 160)
        self.game.obstacles.append(wall)
        self.advance(movement=(1, 1))
        self.assertLessEqual(self.game.tank_pos.x, wall.left - tank_game.TANK_RADIUS)
        self.assertGreater(self.game.tank_pos.y, before.y)

    def test_tank_cannot_drive_through_a_target(self):
        before = self.game.tank_pos.copy()
        target = tank_game.Target(
            before + pygame.Vector2(tank_game.TANK_RADIUS + tank_game.TARGET_RADIUS + 2, 0)
        )
        self.game.targets.append(target)
        self.advance(movement=(1, 0))
        self.assertGreaterEqual(
            self.game.tank_pos.distance_to(target.position),
            tank_game.TANK_RADIUS + tank_game.TARGET_RADIUS,
        )

    def test_turret_follows_mouse_in_each_direction(self):
        for offset, expected in (((100, 0), 0), ((0, 100), 90), ((-100, 0), 180), ((0, -100), -90)):
            with self.subTest(offset=offset):
                self.advance(mouse=self.game.tank_pos + pygame.Vector2(offset))
                angle_difference = (self.game.turret_angle - expected + 180) % 360 - 180
                self.assertAlmostEqual(angle_difference, 0, places=5)

    def test_shooting_uses_mouse_direction_and_has_cooldown(self):
        self.advance(dt=0.01, mouse=self.game.tank_pos + pygame.Vector2(0, -100), firing=True)
        self.assertEqual(self.game.shots_fired, 1)
        self.assertEqual(len(self.game.bullets), 1)
        self.assertAlmostEqual(self.game.bullets[0].velocity.x, 0, places=5)
        self.assertAlmostEqual(self.game.bullets[0].velocity.y, -tank_game.BULLET_SPEED, places=5)
        for _ in range(5):
            self.advance(dt=0.01, firing=True)
        self.assertEqual(self.game.shots_fired, 1)
        for _ in range(20):
            self.advance(dt=0.01, firing=True)
        self.assertEqual(self.game.shots_fired, 2)

    def test_no_shot_when_mouse_button_is_released(self):
        for _ in range(10):
            self.advance(firing=False)
        self.assertEqual(self.game.shots_fired, 0)
        self.assertEqual(self.game.bullets, [])

    def hit_target(self, target):
        self.game.bullets.append(
            tank_game.Bullet(
                target.position - pygame.Vector2(60, 0), pygame.Vector2(tank_game.BULLET_SPEED * 4, 0)
            )
        )
        self.advance()

    def test_target_requires_two_hits_and_awards_one_point(self):
        target = tank_game.Target(self.game.tank_pos + pygame.Vector2(150, 0))
        self.game.targets.append(target)
        self.hit_target(target)
        self.assertEqual(target.health, 1)
        self.assertEqual(self.game.score, 0)
        self.assertIn(target, self.game.targets)
        self.assertEqual(self.game.bullets, [])
        self.hit_target(target)
        self.assertEqual(self.game.score, 1)
        self.assertNotIn(target, self.game.targets)
        self.assertGreater(len(self.game.targets), 0)

    def test_fast_bullet_cannot_skip_a_thin_wall(self):
        center = pygame.Vector2(tank_game.ARENA.center)
        self.game.obstacles.append(pygame.Rect(center.x, center.y - 25, 2, 50))
        self.game.bullets.append(
            tank_game.Bullet(center - pygame.Vector2(20, 0), pygame.Vector2(tank_game.BULLET_SPEED, 0))
        )
        self.advance()
        self.assertEqual(self.game.bullets, [])

    def test_wall_protects_target_in_same_bullet_step(self):
        center = pygame.Vector2(tank_game.ARENA.center)
        target = tank_game.Target(center + pygame.Vector2(40, 0))
        self.game.targets.append(target)
        self.game.obstacles.append(pygame.Rect(center.x - 35, center.y - 30, 6, 60))
        self.game.bullets.append(
            tank_game.Bullet(center - pygame.Vector2(80, 0), pygame.Vector2(tank_game.BULLET_SPEED * 6, 0))
        )
        self.advance()
        self.assertEqual(target.health, 2)
        self.assertEqual(self.game.score, 0)
        self.assertEqual(self.game.bullets, [])

    def test_expired_bullets_are_removed(self):
        self.game.bullets.append(
            tank_game.Bullet(self.game.tank_pos.copy(), pygame.Vector2(10, 0), remaining=0.001)
        )
        self.advance()
        self.assertEqual(self.game.bullets, [])

    def test_target_is_hit_before_a_wall_behind_it(self):
        center = pygame.Vector2(tank_game.ARENA.center)
        target = tank_game.Target(center - pygame.Vector2(30, 0))
        self.game.targets.append(target)
        self.game.obstacles.append(pygame.Rect(center.x + 45, center.y - 30, 6, 60))
        self.game.bullets.append(
            tank_game.Bullet(center - pygame.Vector2(100, 0), pygame.Vector2(tank_game.BULLET_SPEED * 6, 0))
        )
        self.advance()
        self.assertEqual(target.health, 1)
        self.assertEqual(self.game.bullets, [])

    def test_reaching_goal_wins_and_stops_movement_and_shooting(self):
        self.game.score = tank_game.TARGET_GOAL - 1
        target = tank_game.Target(self.game.tank_pos + pygame.Vector2(150, 0), health=1)
        self.game.targets.append(target)
        self.hit_target(target)
        self.assertEqual(self.game.score, tank_game.TARGET_GOAL)
        self.assertTrue(self.game.won)
        before = self.game.tank_pos.copy()
        shots_before = self.game.shots_fired
        self.advance(movement=(1, 0), firing=True)
        self.assertEqual(self.game.tank_pos, before)
        self.assertEqual(self.game.shots_fired, shots_before)

    def test_restart_key_resets_round(self):
        self.game.score = 7
        self.game.shots_fired = 14
        self.game.elapsed = 30
        self.game.won = True
        self.game.bullets.append(tank_game.Bullet(self.game.tank_pos.copy(), pygame.Vector2(10, 0)))
        self.game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r))
        self.assertEqual(self.game.score, 0)
        self.assertEqual(self.game.shots_fired, 0)
        self.assertEqual(self.game.elapsed, 0)
        self.assertFalse(self.game.won)
        self.assertEqual(self.game.bullets, [])
        self.assertGreater(len(self.game.targets), 0)

    def test_close_and_escape_events_stop_game(self):
        for event in (pygame.event.Event(pygame.QUIT), pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)):
            with self.subTest(event=event):
                self.game.running = True
                self.game.handle_event(event)
                self.assertFalse(self.game.running)

    def test_draws_active_and_completed_rounds(self):
        surface = pygame.Surface((tank_game.WIDTH, tank_game.HEIGHT))
        self.game.reset()
        self.game.draw(surface)
        self.assertGreater(len(set(pygame.image.tostring(surface, "RGB"))), 8)
        self.game.won = True
        self.game.score = tank_game.TARGET_GOAL
        self.game.draw(surface)


if __name__ == "__main__":
    unittest.main()
