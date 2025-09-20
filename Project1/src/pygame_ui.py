"""
What this file does:
- Opens a Pygame window with a 5x5 grid (terrain colors, base border, resource letters).
- Lets you switch maps (A/B/C), choose a heuristic (Main or Zero/Dijkstra), and run A*.
- Draws the optimal path and shows metrics in a right side panel.

Keys:
  M      Switch map (A -> B -> C)
  1/0     Use Main heuristic/ Dijkstra h
  R      Solve (run A*)
  C      Clear result
  ESC    Quit
"""

# ==== 1) Imports =================================================================

import sys
import pygame
from typing import Tuple, List, Optional
from grid import (
    Grid,
    TERRAIN_GRASS, TERRAIN_HILL, TERRAIN_SWAMP, TERRAIN_MOUNTAIN,
)
from mapABC import map_A, map_B, map_C
from aGraphStart import astar_solve

# Heuristics
from heuristic import heuristic, heuristic_zero


# ==== 2) Layout & sizing ==========================================================

ROWS = 5
COLS = 5

CELL = 80
MARGIN = 10
PANEL_W = 300

GRID_W = CELL * COLS
GRID_H = CELL * ROWS
WIN_W = MARGIN * 2 + GRID_W + PANEL_W

# Extra panel height so all info (status, controls, legend, metrics) fits
EXTRA_PANEL_H = 130
WIN_H = MARGIN * 2 + GRID_H + EXTRA_PANEL_H


# ==== 3) Colors (pastel palette) =================================================

BG = (255, 245, 250)      # window background (blush)
BLACK = (10, 10, 10)
WHITE = (255, 255, 255)
TEXT = (74, 44, 76)       # plum for panel text
BORDER = (230, 183, 210)  # soft pink borders

# Terrain colors
COLOR_GRASS    = (200, 247, 220)  # mint
COLOR_HILL     = (255, 209, 220)  # peachy pink
COLOR_SWAMP    = (220, 199, 255)  # lavender
COLOR_MOUNTAIN = (201, 178, 191)  # mauve/rose gray

# Base, resources, and path
BASE_BORDER   = (255, 105, 180)   # hot pink border for base (0,0)
RESOURCE_TEXT = (80, 35, 90)      # resource letters S/I/C in plum

PATH_COLOR = (255, 77, 166)       # fuchsia path line
PATH_NODE  = (255, 105, 180)      # hot pink path nodes

# Terrain color mapping used while drawing the grid
TERRAIN_TO_COLOR = {
    TERRAIN_GRASS:    COLOR_GRASS,
    TERRAIN_HILL:     COLOR_HILL,
    TERRAIN_SWAMP:    COLOR_SWAMP,
    TERRAIN_MOUNTAIN: COLOR_MOUNTAIN,
}


# ==== 4) Drawing helpers (grid geometry) =========================================

def cell_rect(r: int, c: int) -> pygame.Rect:
    """Grid (row, col) -> pygame.Rect on the screen."""
    x = MARGIN + c * CELL
    y = MARGIN + r * CELL
    return pygame.Rect(x, y, CELL, CELL)


def cell_center(r: int, c: int) -> Tuple[int, int]:
    """Center (x, y) of a grid cell."""
    rect = cell_rect(r, c)
    return rect.centerx, rect.centery


# ==== 5) Grid & path rendering ====================================================

def draw_grid_background(surface: pygame.Surface, grid: Grid) -> None:
    """Terrain fill, base border, and thin grid lines (NO letters)."""
    for r in range(ROWS):
        for c in range(COLS):
            rect = cell_rect(r, c)
            terrain = grid.terrain[r][c]
            pygame.draw.rect(surface, TERRAIN_TO_COLOR[terrain], rect)

            if (r, c) == grid.base:
                pygame.draw.rect(surface, BASE_BORDER, rect, width=4)

            pygame.draw.rect(surface, BORDER, rect, width=1)


def _blit_text_with_outline(surface, text, font, center, fg=RESOURCE_TEXT, outline=(255, 255, 255)):
    """Small readability boost: draw a 1-px outline around the letter."""
    txt = font.render(text, True, fg)
    for dx, dy in ((-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,-1),(-1,1),(1,1)):
        o = font.render(text, True, outline)
        surface.blit(o, o.get_rect(center=(center[0]+dx, center[1]+dy)))
    surface.blit(txt, txt.get_rect(center=center))


def draw_resource_labels(surface: pygame.Surface, grid: Grid, font: pygame.font.Font) -> None:
    """Draw S/I/C letters on top of everything else."""
    # supports grid.resource_on(...) or grid.resource_at(...)
    resource_fn = getattr(grid, "resource_on", None) or getattr(grid, "resource_at", None)
    for r in range(ROWS):
        for c in range(COLS):
            tile = resource_fn((r, c)) if resource_fn else None
            if tile is None:
                continue
            ch = "S" if tile.kind == "STONE" else ("I" if tile.kind == "IRON" else "C")
            _blit_text_with_outline(surface, ch, font, cell_rect(r, c).center)


def draw_path(surface: pygame.Surface, path: Optional[List[Tuple[int, int]]]) -> None:
    """Polyline through cell centers + a dot on each step."""
    if not path or len(path) < 2:
        return
    points = [cell_center(r, c) for (r, c) in path]
    pygame.draw.lines(surface, PATH_COLOR, False, points, width=5)
    for p in points:
        pygame.draw.circle(surface, PATH_NODE, p, 6)

def print_sol_path(result: dict) -> None:
    """Print the optimal path coordinates"""
    if not (result and result.get("solved")):
        print("No solution to print.")
        return
    path = result["path"]
    print("\nOptimal path (row, col):")
    for i, (r, c) in enumerate(path):
        print(f"{i:02d}: ({r},{c})")



# ==== 6) Panel rendering (status, controls, legend, metrics) ======================

def draw_panel(
    surface: pygame.Surface,
    font: pygame.font.Font,
    small: pygame.font.Font,
    map_name: str,
    result: Optional[dict],
    heur_label: str,
) -> None:
    """Right-side info panel."""
    panel = pygame.Rect(MARGIN + GRID_W, MARGIN, PANEL_W, WIN_H - 2 * MARGIN)
    pygame.draw.rect(surface, WHITE, panel)
    pygame.draw.rect(surface, BORDER, panel, width=1)

    y = panel.top + 16
    def line(txt: str, f=font, dy: int = 26, color=TEXT) -> None:
        nonlocal y
        surf = f.render(txt, True, color)
        surface.blit(surf, (panel.left + 16, y))
        y += dy

    # Title
    line(f"Map: {map_name}")
    line(f"Heuristic: {heur_label}", small, dy=22)

    # Status
    if result is None:
        line("Status: ready to solve", small, dy=22)
    else:
        if result.get("solved"):
            line("Status: SOLVED", small, dy=22)
        else:
            line("Status: no solution", small, dy=22)

    # Controls
    y += 8
    line("Controls:", small, dy=22)
    line("  M      Switch map", small, dy=22)
    line("  1/0    Use Main heuristic/ Dijkstra h", small, dy=22)
    line("  R      Solve", small, dy=22)
    line("  C      Clear result", small, dy=22)
    line("  ESC    Quit", small, dy=22)

    # Legend
    y += 8
    line("Legend:", small, dy=22)

    def legend_row(label: str, color: Tuple[int, int, int]) -> None:
        nonlocal y
        sw = 16
        rect = pygame.Rect(panel.left + 16, y + 2, sw, sw)
        pygame.draw.rect(surface, color, rect)
        pygame.draw.rect(surface, BORDER, rect, width=1)
        txt = small.render(f" {label}", True, TEXT)
        surface.blit(txt, (rect.right + 8, y))
        y += 22

    legend_row("Grass", COLOR_GRASS)
    legend_row("Hill", COLOR_HILL)
    legend_row("Swamp", COLOR_SWAMP)
    legend_row("Mountain", COLOR_MOUNTAIN)
    legend_row("Base (0,0) border", BASE_BORDER)
    legend_row("Path", PATH_COLOR)

    # Metrics
    if result and result.get("solved"):
        y += 8
        line("Metrics:", small, dy=22)
        line(f"  Total cost: {result['total_cost']}", small, dy=22)
        line(f"  Path length: {len(result['path']) - 1}", small, dy=22)
        line(f"  Expanded nodes: {result['expanded']}", small, dy=22)
        line(f"  Time: {result['time_ms']:.2f} ms", small, dy=22)
        s, i, c = result["final_state"].delivered
        line(f"  Delivered: S={s} I={i} C={c}", small, dy=22)


# ==== 7) App entrypoint (event loop) ==============================================

def main() -> None:
    """Create the window, handle input, draw frames, and run A* on demand."""
    pygame.init()
    try:
        screen = pygame.display.set_mode((WIN_W, WIN_H))
    except Exception:
        screen = pygame.display.set_mode((WIN_W, WIN_H), flags=pygame.SWSURFACE)
    pygame.display.set_caption("Game")

    font = pygame.font.SysFont("arial", 22)
    small = pygame.font.SysFont("arial", 18)

    # Maps
    maps = [("A", map_A()), ("B", map_B()), ("C", map_C())]
    map_idx = 0
    map_name, grid = maps[map_idx]

    # Heuristic selection
    HEURISTICS = {
        "main": ("Main Heuristic", heuristic),
        "zero": ("Zero (Dijkstra)", heuristic_zero),
    }
    heur_key = "main"

    result: Optional[dict] = None

    # Wrapper to call A* with or without 'heuristic_fn' depending on your astar_solve signature
    def run_astar(g, h_fn):
        try:
            return astar_solve(g, heuristic_fn=h_fn)  # preferred: with heuristic
        except TypeError:
            return astar_solve(g)                     # fallback: no param supported

    clock = pygame.time.Clock()
    running = True
    while running:
        # -- Input handling -------------------------------------------------------
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False

            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    running = False

                elif ev.key == pygame.K_m:
                    map_idx = (map_idx + 1) % len(maps)
                    map_name, grid = maps[map_idx]
                    result = None

                elif ev.key == pygame.K_1:
                    heur_key = "main"
                    result = None

                elif ev.key == pygame.K_0:
                    heur_key = "zero"
                    result = None

                elif ev.key == pygame.K_r:
                    # Solve with the selected heuristic
                    _, h_fn = HEURISTICS[heur_key]
                    result = run_astar(grid, h_fn)
                    #print path in console
                    if result and result.get("solved"):
                        print_sol_path(result)

                elif ev.key == pygame.K_c:
                    result = None

        # -- Drawing --------------------------------------------------------------
        screen.fill(BG)
        draw_grid_background(screen, grid)
        if result and result.get("solved"):
            draw_path(screen, result["path"])
        draw_resource_labels(screen, grid, font)

        label, _ = HEURISTICS[heur_key]
        draw_panel(screen, font, small, map_name, result, label)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


# ==== 8) Run as script ============================================================

if __name__ == "__main__":
    main()
