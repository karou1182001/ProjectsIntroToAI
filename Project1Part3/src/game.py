# ====Imports =================================================================
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
from MinAgents.min_alpha_agent import AlphaBetaAgent


# ==== Layout and  sizing ==========================================================

ROWS = 5
COLS = 5

CELL = 80        
MARGIN = 10      
PANEL_W = 300    

GRID_W = CELL * COLS
GRID_H = CELL * ROWS
WIN_W = MARGIN * 2 + GRID_W + PANEL_W

EXTRA_PANEL_H = 170
WIN_H = MARGIN * 2 + GRID_H + EXTRA_PANEL_H


# ==== Colors  =================================================

BG = (255, 245, 250)      
BLACK = (10, 10, 10)
WHITE = (255, 255, 255)
TEXT = (74, 44, 76)      
BORDER = (230, 183, 210)  

COLOR_GRASS    = (200, 247, 220)  # mint
COLOR_HILL     = (255, 209, 220)  # peachy pink
COLOR_SWAMP    = (220, 199, 255)  # lavender
COLOR_MOUNTAIN = (201, 178, 191)  # rose gray


BASE_A_BORDER  = (255, 105, 180)  
BASE_B_BORDER  = (255, 160, 180)  
RESOURCE_TEXT  = (80, 35, 90)     # S/I/C

PLAYER_A = (255, 105, 180)        
PLAYER_B = (255, 160, 180)        


TERRAIN_TO_COLOR = {
    TERRAIN_GRASS:    COLOR_GRASS,
    TERRAIN_HILL:     COLOR_HILL,
    TERRAIN_SWAMP:    COLOR_SWAMP,
    TERRAIN_MOUNTAIN: COLOR_MOUNTAIN,
}


# ==== Drawing helpers  =========================================

def cell_rect(r: int, c: int) -> pygame.Rect:
    x = MARGIN + c * CELL
    y = MARGIN + r * CELL
    return pygame.Rect(x, y, CELL, CELL)


def cell_center(r: int, c: int) -> Tuple[int, int]:
    rect = cell_rect(r, c)
    return rect.centerx, rect.centery


# ==== Grid & players rendering ================================================

def draw_grid_background(surface: pygame.Surface, grid: Grid) -> None:
    for r in range(ROWS):
        for c in range(COLS):
            rect = cell_rect(r, c)
            terrain = grid.terrain[r][c]
            pygame.draw.rect(surface, TERRAIN_TO_COLOR[terrain], rect)  
            pygame.draw.rect(surface, BORDER, rect, width=1)            


    a_rect = cell_rect(0, 0)
    b_rect = cell_rect(4, 4)
    pygame.draw.rect(surface, BASE_A_BORDER, a_rect, width=4)
    pygame.draw.rect(surface, BASE_B_BORDER, b_rect, width=4)


def _blit_text_with_outline(surface, text, font, center, fg=RESOURCE_TEXT, outline=(255, 255, 255)):
    txt = font.render(text, True, fg)
    # Ocho offsets alrededor para simular contorno.
    for dx, dy in ((-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,-1),(-1,1),(1,1)):
        o = font.render(text, True, outline)
        surface.blit(o, o.get_rect(center=(center[0]+dx, center[1]+dy)))
    surface.blit(txt, txt.get_rect(center=center))


def draw_resource_labels(surface: pygame.Surface, grid: Grid, font: pygame.font.Font, collected_mask: frozenset) -> None:
    for tile in grid.resources:
        if tile.idx in collected_mask:
            continue  
        r, c = tile.pos
        ch = "S" if tile.kind == "STONE" else ("I" if tile.kind == "IRON" else "C")
        _blit_text_with_outline(surface, ch, font, cell_rect(r, c).center)


def draw_players(surface: pygame.Surface, A_pos: Tuple[int,int], B_pos: Tuple[int,int]) -> None:
    def draw_p(rc, color):
        r, c = rc
        pygame.draw.circle(surface, color, cell_center(r, c), CELL//3)

    draw_p(A_pos, PLAYER_A)  
    draw_p(B_pos, PLAYER_B) 


# ==== Panel rendering  ======================

def draw_panel(
    surface: pygame.Surface,
    font: pygame.font.Font,
    small: pygame.font.Font,
    map_name: str,
    ui_state: dict,
) -> None:
    panel = pygame.Rect(MARGIN + GRID_W, MARGIN, PANEL_W, WIN_H - 2 * MARGIN)
    pygame.draw.rect(surface, WHITE, panel)
    pygame.draw.rect(surface, BORDER, panel, width=1)

    y = panel.top + 16
    def line(txt: str, f=font, dy: int = 26, color=TEXT) -> None:
        nonlocal y
        surf = f.render(txt, True, color)
        surface.blit(surf, (panel.left + 16, y))
        y += dy


    line(f"Map: {map_name}")
    opp = "Random" if ui_state["opponent"] == "random" else "Minimax"
    line(f"Opponent: {opp}", small, dy=22)
    status = "PAUSED" if not ui_state["auto"] else "AUTO"
    if ui_state["game_over"]:
        status = "GAME OVER"
    line(f"Status: {status}", small, dy=22)
    line(f"Turn: {ui_state['turn']}", small, dy=22)

    # Controls
    y += 8
    line("Controls:", small, dy=22)
    line("  M      Switch map", small, dy=22)
    line("  1/0    B agent: Random / Minimax", small, dy=22)
    line("  P      Play/Pause", small, dy=22)
    line("  N      Next step", small, dy=22)
    line("  C      Reset", small, dy=22)
    line("  ESC    Quit", small, dy=22)

    # Legends
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

    # Metrics
    y += 8
    line("Metrics:", small, dy=22)
    line(f"  A delivered: {ui_state['A_del']}  bag: {ui_state['A_bag']}", small, dy=22)
    line(f"  B delivered: {ui_state['B_del']}  bag: {ui_state['B_bag']}", small, dy=22)
    line(f"  Remaining on map: {ui_state['remaining']}", small, dy=22)
    if ui_state["last_decision_ms"] is not None:
        line(f"  Last AI decide: {ui_state['last_decision_ms']:.2f} ms", small, dy=22)
    if ui_state["game_over"]:
        # Finish
        result = "Tie!"
        if ui_state["A_del"] > ui_state["B_del"]:
            result = "A wins!"
        elif ui_state["B_del"] > ui_state["A_del"]:
            result = "B wins!"
        line(f"  Result: {result}", small, dy=22)


# ==== Game loop helpers ========================================================
def step_turn(state, A_agent, B_agent):
    """
    Ejecuta exactamente un turno (A o B, según corresponda):
    - Si terminal, devuelve tal cual.
    - Llama decide_move del agente en turno (mide el tiempo).
    - Aplica el movimiento con 'apply_move' (que alterna el turno internamente).
    - Retorna (nuevo_estado, es_terminal, ms_decision_ultima_jugada).
    """
    if state.is_terminal():
        return state, True, None

    last_ms = None
    if state.turn == "A":
        t0 = time.perf_counter()
        mv = A_agent.decide_move(state)                      
        last_ms = (time.perf_counter() - t0) * 1000.0
        if mv is None:                                        
            return state, True, last_ms
        state = apply_move(state, mv)                        
    else:
        t0 = time.perf_counter()
        mv = B_agent.decide_move(state)                      
        last_ms = (time.perf_counter() - t0) * 1000.0
        if mv is None:
            return state, True, last_ms
        state = apply_move(state, mv)

    return state, state.is_terminal(), last_ms


# ====  App Main  ==============================================

def main() -> None:
    pygame.init()
    try:
        screen = pygame.display.set_mode((WIN_W, WIN_H))
    except Exception:
        screen = pygame.display.set_mode((WIN_W, WIN_H), flags=pygame.SWSURFACE)
    pygame.display.set_caption("Competitive Grid — Minimax")

    
    font = pygame.font.SysFont("arial", 22)
    small = pygame.font.SysFont("arial", 18)

    
    maps = [("A", map_A()), ("B", map_B()), ("C", map_C())]
    map_idx = 0
    map_name, grid = maps[map_idx]

    # Agents: A  Minimax  B  Random and Minimax 
    A_agent = AlphaBetaAgent(depth=5)
    B_kind = "random"  
    B_agent = RandomAgent()

    state = initial_state(grid)

    
    auto = False                      
    game_over = False                
    last_decision_ms: Optional[float] = None   

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
                    map_idx = (map_idx + 1) % len(maps)
                    map_name, grid = maps[map_idx]
                    state = initial_state(grid)
                    game_over = False
                    last_decision_ms = None
                    auto = False

                elif ev.key == pygame.K_1:
                    B_kind = "random"
                    B_agent = RandomAgent()
                    state = initial_state(grid)
                    game_over = False
                    last_decision_ms = None
                    auto = False

                elif ev.key == pygame.K_0:
                    B_kind = "minimax"
                    B_agent = AlphaBetaAgent(depth=4)
                    state = initial_state(grid)
                    game_over = False
                    last_decision_ms = None
                    auto = False

                elif ev.key == pygame.K_p:
                    auto = not auto and not game_over

                elif ev.key == pygame.K_n:
                    if not auto and not game_over:
                        state, game_over, last_decision_ms = step_turn(state, A_agent, B_agent)

                elif ev.key == pygame.K_c:
                    state = initial_state(grid)
                    game_over = False
                    last_decision_ms = None
                    auto = False

        # -- Auto play ------------------------------------------------------------
        if auto and not game_over:
            state, game_over, last_decision_ms = step_turn(state, A_agent, B_agent)

        # -- Drawing --------------------------------------------------------------
        screen.fill(BG)
        draw_grid_background(screen, state.grid)
        draw_resource_labels(screen, state.grid, font, state.collected_mask)
        draw_players(screen, state.A.pos, state.B.pos)

        
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

        
        pygame.display.flip()
        clock.tick(60)

    # Salida limpia
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
