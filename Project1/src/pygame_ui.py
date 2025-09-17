"""
What this file does:
- Opens a Pygame window with a 5x5 grid (terrain colors, base border, resource letters).
- Lets you switch maps (A/B/C), pick a heuristic (h1/h3), and run A*.
- Draws the optimal path and shows metrics in a right side panel.

Keys:
  M      Switch map (A -> B -> C)
  1 / 3  Select heuristic h1 / h3
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
from maps import build_map_A, build_map_B, build_map_C
from astar import astar_solve


# ==== 2) Layout & sizing ==========================================================

ROWS = 5                      # grid rows
COLS = 5                      # grid cols

CELL = 80                     # size of each cell in pixels
MARGIN = 10                   # outer margin around the grid (all sides)
PANEL_W = 300                 # width of the right-side info panel

GRID_W = CELL * COLS
GRID_H = CELL * ROWS
WIN_W = MARGIN * 2 + GRID_W + PANEL_W

# Extra panel height so all info (status, controls, legend, metrics) fits 
EXTRA_PANEL_H = 120
WIN_H = MARGIN * 2 + GRID_H + EXTRA_PANEL_H


# ==== 3) Colors (pastel palette) ========================================

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
    """
    Convert a grid coordinate (row, col) to a pygame.Rect on the screen.
    The rect spans exactly one grid cell.
    """
    x = MARGIN + c * CELL
    y = MARGIN + r * CELL
    return pygame.Rect(x, y, CELL, CELL)


def cell_center(r: int, c: int) -> Tuple[int, int]:
    """
    Return the (x, y) pixel coordinates of the center of a grid cell.
    Useful for drawing the path through cell centers.
    """
    rect = cell_rect(r, c)
    return rect.centerx, rect.centery


# ==== 5) Grid & path rendering ====================================================

def draw_grid(surface: pygame.Surface, grid: Grid, font: pygame.font.Font) -> None:
    """
    Draw the 5x5 grid:
      - fill each cell with its terrain color,
      - overlay resource letters (S/I/C) when present,
      - draw a thick hot-pink border for the Base at (0,0),
      - draw thin borders for the cell grid lines.
    """
    for r in range(ROWS):
        for c in range(COLS):
            rect = cell_rect(r, c)
            terrain = grid.terrain[r][c]

            # cell fill by terrain color
            pygame.draw.rect(surface, TERRAIN_TO_COLOR[terrain], rect)

            # overlay resource letter (if any)
            tile = grid.resource_at((r, c))
            if tile is not None:
                ch = "S" if tile.kind == "STONE" else ("I" if tile.kind == "IRON" else "C")
                text_surf = font.render(ch, True, RESOURCE_TEXT)
                surface.blit(text_surf, text_surf.get_rect(center=rect.center))

            # draw base border on (0,0)
            if (r, c) == grid.base:
                pygame.draw.rect(surface, BASE_BORDER, rect, width=4)

            # thin grid line
            pygame.draw.rect(surface, BORDER, rect, width=1)


def draw_path(surface: pygame.Surface, path: Optional[List[Tuple[int, int]]]) -> None:
    """
    Draw the solution path as:
      - a polyline through the centers of the visited cells,
      - filled circles at each step for extra clarity.
    """
    if not path or len(path) < 2:
        return

    points = [cell_center(r, c) for (r, c) in path]

    # polyline
    pygame.draw.lines(surface, PATH_COLOR, False, points, width=5)

    # node dots
    for p in points:
        pygame.draw.circle(surface, PATH_NODE, p, 6)


# ==== 6) Panel rendering (status, controls, legend, metrics) ======================

def draw_panel(
    surface: pygame.Surface,
    font: pygame.font.Font,
    small: pygame.font.Font,
    map_name: str,
    heuristic: str,
    result: Optional[dict],
) -> None:
    """
    Render the right-side panel. It shows:
      - current map and heuristic
      - status (ready/solved/no solution)
      - controls
      - legend (what each terrain color means)
      - metrics (only when solved)
    """
    # Panel rectangle sized to the full window height minus margins
    panel = pygame.Rect(MARGIN + GRID_W, MARGIN, PANEL_W, WIN_H - 2 * MARGIN)
    pygame.draw.rect(surface, WHITE, panel)
    pygame.draw.rect(surface, BORDER, panel, width=1)

    # Simple text helper to stack lines downward
    y = panel.top + 16
    def line(txt: str, f=font, dy: int = 26, color=TEXT) -> None:
        nonlocal y
        surf = f.render(txt, True, color)
        surface.blit(surf, (panel.left + 16, y))
        y += dy

    # Title
    line(f"Map: {map_name}")
    line(f"Heuristic: {heuristic}", small, dy=22)

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
    line("  1 / 3  Select h1 / h3", small, dy=22)
    line("  R      Solve", small, dy=22)
    line("  C      Clear result", small, dy=22)
    line("  ESC    Quit", small, dy=22)

    # Legend (terrain meaning)
    y += 8
    line("Legend:", small, dy=22)

    def legend_row(label: str, color: Tuple[int, int, int]) -> None:
        nonlocal y
        sw = 16  # swatch size
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

    # Metrics (only if we have a solved result)
    if result and result.get("solved"):
        y += 8
        line("Metrics:", small, dy=22)
        line(f"  Total cost: {result['total_cost']}", small, dy=22)
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
        # Fallback in case of GPU/driver issues
        screen = pygame.display.set_mode((WIN_W, WIN_H), flags=pygame.SWSURFACE)
    pygame.display.set_caption("Game")

    # Fonts for normal text and smaller text
    font = pygame.font.SysFont("arial", 22)
    small = pygame.font.SysFont("arial", 18)

    # Build available maps and start on A
    maps = [("A", build_map_A()), ("B", build_map_B()), ("C", build_map_C())]
    map_idx = 0
    map_name, grid = maps[map_idx]

    heuristic = "h3"            # default heuristic
    result: Optional[dict] = None   # will store the dict returned by astar_solve

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
                    # Switch map and clear current result
                    map_idx = (map_idx + 1) % len(maps)
                    map_name, grid = maps[map_idx]
                    result = None

                elif ev.key == pygame.K_1:
                    heuristic = "h1"  # pick heuristic h1 (won't solve yet)
                elif ev.key == pygame.K_3:
                    heuristic = "h3"  # pick heuristic h3 (won't solve yet)

                elif ev.key == pygame.K_r:
                    # Run A* now with the selected heuristic
                    result = astar_solve(grid, heuristic_name=heuristic)

                elif ev.key == pygame.K_c:
                    # Clear last result (hide path/metrics)
                    result = None

        # -- Drawing --------------------------------------------------------------
        screen.fill(BG)                  # window background
        draw_grid(screen, grid, font)    # terrain, resources, base

        # If we have a solved result, draw the path on top of the grid
        if result and result.get("solved"):
            draw_path(screen, result["path"])

        # Right-side info panel
        draw_panel(screen, font, small, map_name, heuristic, result)

        pygame.display.flip()
        clock.tick(60)  

    pygame.quit()
    sys.exit()


# ==== 8) Run as script ============================================================

if __name__ == "__main__":
    main()
