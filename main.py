"""Run the tank game: python main.py."""

import argparse
import os
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Iron Range: a small 2D tank game.")
    parser.add_argument("--headless", action="store_true", help="Use a virtual display.")
    parser.add_argument("--frames", type=int, help="Exit after this many frames.")
    parser.add_argument("--screenshot", type=Path, help="Save the final frame as a PNG.")
    args = parser.parse_args()
    if args.frames is not None and args.frames < 1:
        parser.error("--frames must be at least 1")
    if args.headless and args.frames is None:
        parser.error("--headless requires --frames, for example --frames 120")
    if args.headless:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ["SDL_AUDIODRIVER"] = "dummy"
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

    try:
        import pygame
    except ModuleNotFoundError:
        print("Pygame is missing. Install it with: python -m pip install -r requirements.txt")
        return 1

    from tank_game import Game, HEIGHT, WIDTH

    pygame.display.init()
    pygame.font.init()
    try:
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Iron Range | WASD + Mouse")
        pygame.mouse.set_visible(False)
        clock = pygame.time.Clock()
        game = Game(seed=7 if args.headless else None)
        frame_count = 0
        while game.running:
            dt = 1 / 60 if args.headless else clock.tick(60) / 1000
            for event in pygame.event.get():
                game.handle_event(event)
            if not game.running:
                break
            keys = pygame.key.get_pressed()
            movement = (int(keys[pygame.K_d]) - int(keys[pygame.K_a]),
                        int(keys[pygame.K_s]) - int(keys[pygame.K_w]))
            mouse = (WIDTH * 0.7, HEIGHT * 0.4) if args.headless else pygame.mouse.get_pos()
            firing = pygame.mouse.get_pressed()[0]
            game.update(dt, movement, mouse, firing)
            game.draw(screen)
            pygame.display.flip()
            frame_count += 1
            if args.frames is not None and frame_count >= args.frames:
                break
        if args.screenshot:
            args.screenshot.parent.mkdir(parents=True, exist_ok=True)
            pygame.image.save(screen, str(args.screenshot))
        if args.headless:
            print(f"Rendered {frame_count} frames successfully ({WIDTH} x {HEIGHT}).")
    finally:
        pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
