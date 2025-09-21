# rules.py
from typing import List, Tuple, Optional
from dataclasses import replace
from grid import Grid, LootTile
from state import GameState, Player, A_BASE, B_BASE
from grid import CAPACITY

Coord = Tuple[int, int]

def manhattan(a: Coord, b: Coord) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def neighbors_in_bounds(grid: Grid, pos: Coord) -> List[Coord]:
    r, c = pos
    cand = [(r-1,c), (r+1,c), (r,c-1), (r,c+1)]
    return [p for p in cand if grid.in_bounds(p)]

def legal_moves(state: GameState) -> List[Coord]:
    who = state.turn
    me: Player = state.A if who == "A" else state.B
    return neighbors_in_bounds(state.grid, me.pos)



def _base_of(who: str):
    return A_BASE if who == "A" else B_BASE

def moves_towards_base_if_full(state: GameState) -> List[Coord]:
    """Si la mochila del jugador en turno está llena, devuelve solo movimientos que
    ACERCAN a su base. Si no hay ninguno que acerque, devuelve los legales normales."""
    who = state.turn
    me  = state.A if who == "A" else state.B
    base = _base_of(who)
    all_moves = legal_moves(state)

    if me.bag.count() < CAPACITY:
        return all_moves

    cur = manhattan(me.pos, base)
    better = [m for m in all_moves if manhattan(m, base) < cur]

    # Si hay una movida que entra directamente a base, priorízala (atajo determinista)
    direct = [m for m in better if m == base]
    if direct:
        return direct

    return better if better else all_moves


def _resource_available(state: GameState, at: Coord) -> Optional[LootTile]:
    tile = state.grid.resource_on(at)
    if tile is None:
        return None
    # Solo está disponible si su idx no está en collected_mask
    if tile.idx in state.collected_mask:
        return None
    return tile

def _deliver_if_on_base(state: GameState, who: str, p: Player) -> Tuple[Player, int]:
    # Si está parado en su base, descarga toda la mochila
    is_on_base = (p.pos == (A_BASE if who == "A" else B_BASE))
    if not is_on_base or p.bag.count() == 0:
        return p, 0
    delivered_count = p.bag.count()
    new_p = p.deliver()
    return new_p, delivered_count

def apply_move(state: GameState, dest: Coord) -> GameState:
    """Aplica un movimiento para el jugador del turno:
    - mueve a la celda destino
    - si hay recurso y hay espacio, lo recoge (y lo saca del mapa)
    - si está en base, entrega todo lo que tenga
    """
    who = state.turn
    me: Player = state.A if who == "A" else state.B

    # Mover
    moved = replace(me, pos=dest)

    # Si hay recurso disponible en la celda y tengo espacio, lo recojo
    tile = _resource_available(state, dest)
    new_mask = set(state.collected_mask)
    if tile is not None and not moved.bag.is_full():
        moved = replace(moved, bag=moved.bag.add(tile.kind))
        new_mask.add(tile.idx)  # sacar ese recurso del mapa

    # Si estoy en base, entrego todo
    moved_after_deliver, delivered_now = _deliver_if_on_base(state, who, moved)

    # Actualizar jugador correspondiente y el global delivered
    if who == "A":
        newA = moved_after_deliver
        newB = state.B
    else:
        newA = state.A
        newB = moved_after_deliver

    new_state = replace(
        state,
        A=newA,
        B=newB,
        collected_mask=frozenset(new_mask),
        delivered_total_global=state.delivered_total_global + delivered_now,
    )

    # Cambiar turno
    return new_state.switch_turn()


