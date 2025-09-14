# file: pygame_ui.py
import sys
import pygame
from typing import Tuple, List, Optional

from grid import (
    Grid,
    TERRAIN_GRASS, TERRAIN_HILL, TERRAIN_SWAMP, TERRAIN_MOUNTAIN,
)
from maps import build_map_A, build_map_B, build_map_C
from astar import astar_solve

# -------------------------
# Configuración visual
# -------------------------
CELL = 80               # tamaño de celda en px
MARGIN = 10             # margen alrededor del grid
PANEL_W = 300           # ancho del panel derecho
GRID_W = CELL * 5
GRID_H = CELL * 5
WIN_W = MARGIN*2 + GRID_W + PANEL_W
WIN_H = MARGIN*2 + GRID_H

# Colores
BG = (235, 235, 235)
BLACK = (10, 10, 10)
WHITE = (245, 245, 245)
TEXT = (30, 30, 30)
BORDER = (40, 40, 40)

COLOR_GRASS = (168, 217, 139)     # pradera
COLOR_HILL = (205, 187, 124)      # colina
COLOR_SWAMP = (127, 184, 209)     # pantano
COLOR_MOUNTAIN = (122, 122, 122)  # montaña

BASE_BORDER = (52, 152, 219)      # azul base
RESOURCE_TEXT = (20, 20, 20)      # letras S/I/C

PATH_COLOR = (231, 76, 60)        # rojo ruta
PATH_NODE = (231, 76, 60)

TERRAIN_TO_COLOR = {
    TERRAIN_GRASS: COLOR_GRASS,
    TERRAIN_HILL: COLOR_HILL,
    TERRAIN_SWAMP: COLOR_SWAMP,
    TERRAIN_MOUNTAIN: COLOR_MOUNTAIN,
}

# -------------------------
# Utilidades dibujo y layout
# -------------------------
def cell_rect(r: int, c: int) -> pygame.Rect:
    x = MARGIN + c * CELL
    y = MARGIN + r * CELL
    return pygame.Rect(x, y, CELL, CELL)

def cell_center(r: int, c: int) -> Tuple[int, int]:
    rect = cell_rect(r, c)
    return rect.centerx, rect.centery

def draw_grid(surface: pygame.Surface, grid: Grid, font: pygame.font.Font):
    # Terrenos y recursos
    for r in range(5):
        for c in range(5):
            rect = cell_rect(r, c)
            t = grid.terrain[r][c]
            pygame.draw.rect(surface, TERRAIN_TO_COLOR[t], rect)

            # Recurso encima (S/I/C)
            tile = grid.resource_at((r, c))
            if tile is not None:
                ch = "S" if tile.kind == "STONE" else ("I" if tile.kind == "IRON" else "C")
                text_surf = font.render(ch, True, RESOURCE_TEXT)
                surface.blit(text_surf, text_surf.get_rect(center=rect.center))

            # Base en (0,0) con borde especial
            if (r, c) == grid.base:
                pygame.draw.rect(surface, BASE_BORDER, rect, width=4)

            # Rejilla (líneas)
            pygame.draw.rect(surface, BORDER, rect, width=1)

def draw_path(surface: pygame.Surface, path: Optional[List[Tuple[int,int]]]):
    """Dibuja una polilínea por el centro de las celdas del path y marca nodos."""
    if not path or len(path) < 2:
        return
    points = [cell_center(r, c) for (r, c) in path]
    # Línea
    pygame.draw.lines(surface, PATH_COLOR, False, points, width=5)
    # Puntos
    for p in points:
        pygame.draw.circle(surface, PATH_NODE, p, 6)

def draw_panel(surface: pygame.Surface, font: pygame.font.Font, small: pygame.font.Font,
               map_name: str, heuristic: str, result: Optional[dict]):
    # Panel derecho
    panel = pygame.Rect(MARGIN + GRID_W, MARGIN, PANEL_W, GRID_H)
    pygame.draw.rect(surface, WHITE, panel)
    pygame.draw.rect(surface, BORDER, panel, width=1)

    y = panel.top + 16
    def line(txt, f=font, dy=26, color=TEXT):
        nonlocal y
        surf = f.render(txt, True, color)
        surface.blit(surf, (panel.left + 16, y))
        y += dy

    # Título
    line(f"Map: {map_name}")
    line(f"Heurística: {heuristic}", small, dy=22)

    # Estado
    if result is None:
        line("Estado: listo para resolver", small, dy=22)
    else:
        if result.get("solved"):
            line("Estado: SOLVED ✓", small, dy=22)
        else:
            line("Estado: sin solución", small, dy=22)

    y += 8
    line("Controles:", small, dy=22)
    line("  M      Cambiar mapa", small, dy=22)
    line("  1 / 3  Elegir h1 / h3", small, dy=22)
    line("  R      Resolver", small, dy=22)
    line("  C      Limpiar resultado", small, dy=22)
    line("  ESC    Salir", small, dy=22)

    # Métricas si hay resultado
    if result and result.get("solved"):
        y += 8
        line("Métricas:", small, dy=22)
        line(f"  Costo total: {result['total_cost']}", small, dy=22)
        line(f"  Nodos exp.: {result['expanded']}", small, dy=22)
        line(f"  Tiempo: {result['time_ms']:.2f} ms", small, dy=22)
        s,i,c = result["final_state"].delivered
        line(f"  Entregado: S={s} I={i} C={c}", small, dy=22)

def main():
    pygame.init()
    try:
        screen = pygame.display.set_mode((WIN_W, WIN_H))
    except Exception:
        # Fallback por si hay problemas con aceleración
        screen = pygame.display.set_mode((WIN_W, WIN_H), flags=pygame.SWSURFACE)
    pygame.display.set_caption("Grid Resource A* — GUI")

    font = pygame.font.SysFont("arial", 22)
    small = pygame.font.SysFont("arial", 18)

    # Mapas disponibles
    maps = [("A", build_map_A()), ("B", build_map_B()), ("C", build_map_C())]
    map_idx = 0
    map_name, grid = maps[map_idx]

    heuristic = "h3"    # por defecto
    result: Optional[dict] = None  # guardaremos aquí el dict que devuelve astar_solve

    clock = pygame.time.Clock()
    running = True
    while running:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    running = False

                elif ev.key == pygame.K_m:
                    # Cambiar mapa y limpiar resultado
                    map_idx = (map_idx + 1) % len(maps)
                    map_name, grid = maps[map_idx]
                    result = None

                elif ev.key == pygame.K_1:
                    heuristic = "h1"
                    # no resolvemos aún; espera R
                elif ev.key == pygame.K_3:
                    heuristic = "h3"

                elif ev.key == pygame.K_r:
                    # Ejecutar A*
                    result = astar_solve(grid, heuristic_name=heuristic)

                elif ev.key == pygame.K_c:
                    result = None

        # Fondo
        screen.fill(BG)

        # Dibujo del grid
        draw_grid(screen, grid, font)

        # Si hay resultado con ruta, dibújala encima
        if result and result.get("solved"):
            draw_path(screen, result["path"])

        # Panel lateral
        draw_panel(screen, font, small, map_name, heuristic, result)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
