"""

What this file does:
- Opens a Pygame window with a 5x5 grid (pastel terrain, base borders, resource letters).
- Lets you switch maps (A/B/C), choose the opponent (Random or Minimax), and run the match.
- Draws players A/B, shows status/metrics in a right side panel, and supports step/auto play.

Keys:
  M      Switch map (A -> B -> C)
  1/0    Opponent: 1 = Random, 0 = Minimax
  R      Play/Pause (auto)
  N      Next step (one turn)
  C      Clear / Reset current map
  ESC    Quit
"""

# ==== 1) Imports =================================================================
# Librerías estándar y de terceros + módulos del proyecto que definen el mundo,
# generación de mapas, estado inicial, reglas de transición y agentes.

import sys
import time
import pygame
from typing import Tuple, List, Optional

from grid import (
    Grid,
    TERRAIN_GRASS, TERRAIN_HILL, TERRAIN_SWAMP, TERRAIN_MOUNTAIN,
)
from mapABC import map_A, map_B, map_C           # Generadores de mapas A/B/C (5x5)
from status import initial_state                  # Crea el estado inicial del juego
from conditions import apply_move                     # Aplica un movimiento y alterna el turno
from MinAgents.random_agent import RandomAgent   # Agente rival "baseline" aleatorio
from MinAgents.min_alpha_agent import MinimaxAgent # Agente Minimax con poda alpha-beta


# ==== 2) Layout & sizing ==========================================================
# Medidas fijas para el layout de la UI: tamaño de celdas, márgenes y panel lateral.

ROWS = 5
COLS = 5

CELL = 80        # tamaño del lado de cada celda (px)
MARGIN = 10      # espacio entre celdas y bordes
PANEL_W = 300    # ancho del panel lateral derecho

GRID_W = CELL * COLS
GRID_H = CELL * ROWS
WIN_W = MARGIN * 2 + GRID_W + PANEL_W

# Altura extra para que quepan Status/Controls/Legend/Metrics en el panel derecho.
EXTRA_PANEL_H = 170
WIN_H = MARGIN * 2 + GRID_H + EXTRA_PANEL_H


# ==== 3) Colors (pastel palette) =================================================
# Paleta de colores similar a tu viewer de A* para mantener consistencia visual.

BG = (255, 245, 250)      # fondo general ventana
BLACK = (10, 10, 10)
WHITE = (255, 255, 255)
TEXT = (74, 44, 76)       # texto del panel (ciruela)
BORDER = (230, 183, 210)  # líneas de rejilla y bordes del panel

# Colores por tipo de terreno
COLOR_GRASS    = (200, 247, 220)  # mint
COLOR_HILL     = (255, 209, 220)  # peachy pink
COLOR_SWAMP    = (220, 199, 255)  # lavender
COLOR_MOUNTAIN = (201, 178, 191)  # mauve/rose gray

# Bases, recursos y jugadores
BASE_A_BORDER  = (255, 105, 180)  # borde de la base A (0,0)
BASE_B_BORDER  = (255, 160, 180)  # borde de la base B (4,4)
RESOURCE_TEXT  = (80, 35, 90)     # letras S/I/C

PLAYER_A = (255, 105, 180)        # color jugador A
PLAYER_B = (255, 160, 180)         # color jugador B

# Mapeo de tipo de terreno -> color de relleno usado al dibujar
TERRAIN_TO_COLOR = {
    TERRAIN_GRASS:    COLOR_GRASS,
    TERRAIN_HILL:     COLOR_HILL,
    TERRAIN_SWAMP:    COLOR_SWAMP,
    TERRAIN_MOUNTAIN: COLOR_MOUNTAIN,
}


# ==== 4) Drawing helpers (grid geometry) =========================================
# Helpers para convertir coordenadas de grid (r,c) en rectángulos y centros en pantalla.

def cell_rect(r: int, c: int) -> pygame.Rect:
    """Grid (row, col) -> pygame.Rect en coordenadas de ventana."""
    x = MARGIN + c * CELL
    y = MARGIN + r * CELL
    return pygame.Rect(x, y, CELL, CELL)


def cell_center(r: int, c: int) -> Tuple[int, int]:
    """Centro (x, y) de una celda del grid."""
    rect = cell_rect(r, c)
    return rect.centerx, rect.centery


# ==== 5) Grid & players rendering ================================================
# Funciones de renderizado: terreno, bases, etiquetas de recursos y jugadores.

def draw_grid_background(surface: pygame.Surface, grid: Grid) -> None:
    """
    Dibuja:
    - Relleno por terreno con color pastel.
    - Líneas finas de rejilla.
    - Borde de las dos bases (A en (0,0), B en (4,4)).
    No dibuja recursos ni jugadores todavía.
    """
    for r in range(ROWS):
        for c in range(COLS):
            rect = cell_rect(r, c)
            terrain = grid.terrain[r][c]
            pygame.draw.rect(surface, TERRAIN_TO_COLOR[terrain], rect)  # relleno por terreno
            pygame.draw.rect(surface, BORDER, rect, width=1)            # línea fina de celda

    # Bases: solo un borde grueso para identificarlas visualmente
    a_rect = cell_rect(0, 0)
    b_rect = cell_rect(4, 4)
    pygame.draw.rect(surface, BASE_A_BORDER, a_rect, width=4)
    pygame.draw.rect(surface, BASE_B_BORDER, b_rect, width=4)


def _blit_text_with_outline(surface, text, font, center, fg=RESOURCE_TEXT, outline=(255, 255, 255)):
    """
    Dibuja texto con un pequeño contorno de 1 px para legibilidad sobre fondos claros.
    - 'fg': color del texto principal.
    - 'outline': color del contorno (blanco por defecto).
    """
    txt = font.render(text, True, fg)
    # Ocho offsets alrededor para simular contorno.
    for dx, dy in ((-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,-1),(-1,1),(1,1)):
        o = font.render(text, True, outline)
        surface.blit(o, o.get_rect(center=(center[0]+dx, center[1]+dy)))
    surface.blit(txt, txt.get_rect(center=center))


def draw_resource_labels(surface: pygame.Surface, grid: Grid, font: pygame.font.Font, collected_mask: frozenset) -> None:
    """
    Dibuja las letras S/I/C en las celdas que aún contienen recursos (no recogidos).
    - collected_mask: conjunto de índices de recursos ya recogidos (no se muestran).
    """
    for tile in grid.resources:
        if tile.idx in collected_mask:
            continue  # este recurso ya fue recogido
        r, c = tile.pos
        ch = "S" if tile.kind == "STONE" else ("I" if tile.kind == "IRON" else "C")
        _blit_text_with_outline(surface, ch, font, cell_rect(r, c).center)


def draw_players(surface: pygame.Surface, A_pos: Tuple[int,int], B_pos: Tuple[int,int]) -> None:
    """
    Representa A y B como círculos de colores, centrados en sus celdas actuales.
    """
    def draw_p(rc, color):
        r, c = rc
        pygame.draw.circle(surface, color, cell_center(r, c), CELL//3)

    draw_p(A_pos, PLAYER_A)  # Jugador A (azul)
    draw_p(B_pos, PLAYER_B)  # Jugador B (naranja)


# ==== 6) Panel rendering (status, controls, legend, metrics) ======================
# Panel lateral derecho: muestra estado, controles, leyenda visual y métricas de partida.

def draw_panel(
    surface: pygame.Surface,
    font: pygame.font.Font,
    small: pygame.font.Font,
    map_name: str,
    ui_state: dict,
) -> None:
    """
    Dibuja el panel derecho con:
    - Título/estado: mapa, rival elegido, modo (AUTO/PAUSED), turno y fin de juego.
    - Controles de teclado.
    - Leyenda de colores.
    - Métricas básicas (entregados, bolsa, restantes, tiempo última decisión).
    """
    panel = pygame.Rect(MARGIN + GRID_W, MARGIN, PANEL_W, WIN_H - 2 * MARGIN)
    pygame.draw.rect(surface, WHITE, panel)
    pygame.draw.rect(surface, BORDER, panel, width=1)

    y = panel.top + 16
    def line(txt: str, f=font, dy: int = 26, color=TEXT) -> None:
        """Helper para escribir una línea y avanzar 'y' en el panel."""
        nonlocal y
        surf = f.render(txt, True, color)
        surface.blit(surf, (panel.left + 16, y))
        y += dy

    # Título / estado general
    line(f"Map: {map_name}")
    opp = "Random" if ui_state["opponent"] == "random" else "Minimax"
    line(f"Opponent: {opp}", small, dy=22)
    status = "PAUSED" if not ui_state["auto"] else "AUTO"
    if ui_state["game_over"]:
        status = "GAME OVER"
    line(f"Status: {status}", small, dy=22)
    line(f"Turn: {ui_state['turn']}", small, dy=22)

    # Controles
    y += 8
    line("Controls:", small, dy=22)
    line("  M      Switch map", small, dy=22)
    line("  1/0    B agent: Random / Minimax", small, dy=22)
    line("  P      Play/Pause", small, dy=22)
    line("  N      Next step", small, dy=22)
    line("  C      Reset", small, dy=22)
    line("  ESC    Quit", small, dy=22)

    # Leyenda de colores/roles
    y += 8
    line("Legend:", small, dy=22)

    def legend_row(label: str, color: Tuple[int, int, int]) -> None:
        """Dibuja una pequeña muestra de color + etiqueta."""
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
    legend_row("Base A (0,0)", BASE_A_BORDER)
    legend_row("Base B (4,4)", BASE_B_BORDER)

    # Métricas en vivo de la partida
    y += 8
    line("Metrics:", small, dy=22)
    line(f"  A delivered: {ui_state['A_del']}  bag: {ui_state['A_bag']}", small, dy=22)
    line(f"  B delivered: {ui_state['B_del']}  bag: {ui_state['B_bag']}", small, dy=22)
    line(f"  Remaining on map: {ui_state['remaining']}", small, dy=22)
    if ui_state["last_decision_ms"] is not None:
        line(f"  Last AI decide: {ui_state['last_decision_ms']:.2f} ms", small, dy=22)
    if ui_state["game_over"]:
        # Mensaje de resultado al finalizar
        result = "Tie!"
        if ui_state["A_del"] > ui_state["B_del"]:
            result = "A wins!"
        elif ui_state["B_del"] > ui_state["A_del"]:
            result = "B wins!"
        line(f"  Result: {result}", small, dy=22)


# ==== 7) Game loop helpers ========================================================
# Helper para ejecutar "exactamente un turno": consulta al agente correspondiente,
# aplica el movimiento, mide tiempo de decisión y detecta si la partida terminó.

def step_turn(state, A_agent, B_agent):
    """
    Ejecuta exactamente un turno (A o B, según corresponda):
    - Si terminal, devuelve tal cual.
    - Llama select_move del agente en turno (mide el tiempo).
    - Aplica el movimiento con 'apply_move' (que alterna el turno internamente).
    - Retorna (nuevo_estado, es_terminal, ms_decision_ultima_jugada).
    """
    if state.is_terminal():
        return state, True, None

    last_ms = None
    if state.turn == "A":
        t0 = time.perf_counter()
        mv = A_agent.select_move(state)                       # A decide
        last_ms = (time.perf_counter() - t0) * 1000.0
        if mv is None:                                        # sin movimiento válido -> fin
            return state, True, last_ms
        state = apply_move(state, mv)                         # aplica y alterna turno
    else:
        t0 = time.perf_counter()
        mv = B_agent.select_move(state)                       # B decide
        last_ms = (time.perf_counter() - t0) * 1000.0
        if mv is None:
            return state, True, last_ms
        state = apply_move(state, mv)

    return state, state.is_terminal(), last_ms


# ==== 8) App entrypoint (event loop) ==============================================
# Bucle principal: inicializa Pygame, crea ventana, maneja input, dibuja cada frame
# y orquesta el avance del juego (auto o paso-a-paso).

def main() -> None:
    """Crea la ventana, maneja input, dibuja frames y ejecuta el match competitivo."""
    pygame.init()
    try:
        screen = pygame.display.set_mode((WIN_W, WIN_H))
    except Exception:
        # Fallback para entornos donde el flag por defecto puede fallar
        screen = pygame.display.set_mode((WIN_W, WIN_H), flags=pygame.SWSURFACE)
    pygame.display.set_caption("Competitive Grid — Minimax")

    # Fuentes para textos del panel
    font = pygame.font.SysFont("arial", 22)
    small = pygame.font.SysFont("arial", 18)

    # Mapas disponibles y selección actual
    maps = [("A", map_A()), ("B", map_B()), ("C", map_C())]
    map_idx = 0
    map_name, grid = maps[map_idx]

    # Agentes: A es Minimax; B puede alternar entre Random y Minimax (teclas 1/0)
    A_agent = MinimaxAgent(depth=4)
    B_kind = "random"  # o "minimax"
    B_agent = RandomAgent()

    # Estado inicial de la partida (posiciones, mochilas, turnos, etc.)
    state = initial_state(grid)

    # Flags de UI
    auto = False                      # modo automático (Play/Pause)
    game_over = False                 # fin de partida
    last_decision_ms: Optional[float] = None   # tiempo de la última decisión del agente

    clock = pygame.time.Clock()
    running = True
    while running:
        # -- Input handling -------------------------------------------------------
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False

            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    # Salir de la aplicación
                    running = False

                elif ev.key == pygame.K_m:
                    # Cambiar de mapa y re-inicializar estado/flags
                    map_idx = (map_idx + 1) % len(maps)
                    map_name, grid = maps[map_idx]
                    state = initial_state(grid)
                    game_over = False
                    last_decision_ms = None
                    auto = False

                elif ev.key == pygame.K_1:
                    # Rival = Random, reinicia partida en el mapa actual
                    B_kind = "random"
                    B_agent = RandomAgent()
                    state = initial_state(grid)
                    game_over = False
                    last_decision_ms = None
                    auto = False

                elif ev.key == pygame.K_0:
                    # Rival = Minimax, reinicia partida en el mapa actual
                    B_kind = "minimax"
                    B_agent = MinimaxAgent(depth=4)
                    state = initial_state(grid)
                    game_over = False
                    last_decision_ms = None
                    auto = False

                elif ev.key == pygame.K_p:
                    # Play/Pause: sólo alterna si la partida no terminó
                    auto = not auto and not game_over

                elif ev.key == pygame.K_n:
                    # Un único turno si está pausado y no terminó
                    if not auto and not game_over:
                        state, game_over, last_decision_ms = step_turn(state, A_agent, B_agent)

                elif ev.key == pygame.K_c:
                    # Reset duro: reinicia estado en el mapa actual
                    state = initial_state(grid)
                    game_over = False
                    last_decision_ms = None
                    auto = False

        # -- Auto play ------------------------------------------------------------
        # Si está en modo AUTO y no terminó, avanza turnos automáticamente
        if auto and not game_over:
            state, game_over, last_decision_ms = step_turn(state, A_agent, B_agent)

        # -- Drawing --------------------------------------------------------------
        # Limpiar fondo y dibujar tablero/recursos/jugadores
        screen.fill(BG)
        draw_grid_background(screen, state.grid)
        draw_resource_labels(screen, state.grid, font, state.collected_mask)
        draw_players(screen, state.A.pos, state.B.pos)

        # Construir datos del panel y dibujarlo
        ui_state = {
            "opponent": B_kind,
            "auto": auto,
            "game_over": game_over,
            "turn": state.turn,
            "A_del": state.A.delivered_total,
            "A_bag": state.A.bag.count(),
            "B_del": state.B.delivered_total,
            "B_bag": state.B.bag.count(),
            "remaining": len(state.grid.resources) - len(state.collected_mask),
            "last_decision_ms": last_decision_ms,
        }
        draw_panel(screen, font, small, map_name, ui_state)

        # Flip de pantalla y sincronización de FPS
        pygame.display.flip()
        clock.tick(60)

    # Salida limpia
    pygame.quit()
    sys.exit()


# ==== 9) Run as script ============================================================
# Permite ejecutar este archivo directamente: `python game.py`

if __name__ == "__main__":
    main()
