"""
What this file does:
- Opens a Pygame window with a 5x5 grid (terrain colors, base border, resource letters).
- Lets you switch maps (A/B/C), and run A*.
- Draws the optimal path and shows metrics in a right side panel.

Keys:
  M      Switch map (A -> B -> C)
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
    # Outline passes
    for dx, dy in ((-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,-1),(-1,1),(1,1)):
        o_surf = font.render(text, True, outline)
        surface.blit(o_surf, o_surf.get_rect(center=(center[0]+dx, center[1]+dy)))
    # Main glyph
    surface.blit(txt, txt.get_rect(center=center))


def draw_resource_labels(surface: pygame.Surface, grid: Grid, font: pygame.font.Font) -> None:
    """Draw S/I/C letters on top of everything else."""
    for r in range(ROWS):
        for c in range(COLS):
            tile = getattr(grid, "resource_on", getattr(grid, "resource_on"))((r, c))
            if tile is None:
                continue
            ch = "S" if tile.kind == "STONE" else ("I" if tile.kind == "IRON" else "C")
            _blit_text_with_outline(surface, ch, font, cell_rect(r, c).center)



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
    result: Optional[dict],
) -> None:
    """
    Render the right-side panel. It shows:
      - current map 
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
        # Fallback in case of GPU/driver issues
        screen = pygame.display.set_mode((WIN_W, WIN_H), flags=pygame.SWSURFACE)
    pygame.display.set_caption("Game")

    # Fonts for normal text and smaller text
    font = pygame.font.SysFont("arial", 22)
    small = pygame.font.SysFont("arial", 18)

    # Build available maps and start on A
    maps = [("A", map_A()), ("B", map_B()), ("C", map_C())]
    map_idx = 0
    map_name, grid = maps[map_idx]

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

                elif ev.key == pygame.K_r:
                    # Run A* now with the selected
                    result = astar_solve(grid)

                elif ev.key == pygame.K_c:
                    # Clear last result (hide path/metrics)
                    result = None

        # -- Drawing --------------------------------------------------------------
        screen.fill(BG)                  # window background
        draw_grid_background(screen, grid)
        if result and result.get("solved"):
            draw_path(screen, result["path"])
        draw_resource_labels(screen, grid, font)
        # Right-side info panel
        draw_panel(screen, font, small, map_name, result)

        pygame.display.flip()
        clock.tick(60)  

    pygame.quit()
    sys.exit()


# ==== 8) Run as script ============================================================

if __name__ == "__main__":
    main()
