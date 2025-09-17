# file: transitions.py
from typing import List, Tuple, Optional
from grid import Grid, CAPACITY, RES_STONE, RES_IRON, RES_CRYSTAL
from state import State, backpack_tuple, apply_deposit

Action = Tuple[int, int]  # (dr, dc) desplazamiento relativo

ACTIONS: List[Action] = [
    (-1, 0),  # norte
    ( 1, 0),  # sur
    ( 0,-1),  # oeste
    ( 0, 1),  # este
]

def _is_adjacent(a: Tuple[int,int], b: Tuple[int,int]) -> bool:
    """Valida si b está a una distancia Manhattan 1 de a (movimiento 4-dir)."""
    return abs(a[0]-b[0]) + abs(a[1]-b[1]) == 1

def step_transition(grid: Grid, s: State, dest: Tuple[int,int]) -> Optional[Tuple[State, int]]:
    """
    Aplica UNA transición (s -> s2) moviéndose a 'dest' si es adyacente y está dentro del grid.
    Reglas:
      - Costo del paso = costo del TERRENO de destino.
      - Si el destino es la BASE y hay items en mochila -> DEPOSITA automático.
      - Si el destino tiene un recurso NO consumido y hay espacio -> RECOGE automático.
    Devuelve (nuevo_estado, costo_del_paso) o None si el movimiento no es válido.
    """
    # 1) Validaciones de movimiento
    if not grid.in_bounds(dest) or not _is_adjacent(s.pos, dest):
        return None

    step_cost = grid.terrain_cost(dest)

    # 2) Copias mutables para construir s2
    new_bp = list(s.backpack)
    new_deliv = {
        RES_STONE:  s.delivered[0],
        RES_IRON:   s.delivered[1],
        RES_CRYSTAL:s.delivered[2],
    }
    new_mask = s.consumed_mask

    # 3) Depósito automático si pisas la base con items en mochila
    if dest == grid.base and new_bp:
        bp_after, delivered_tuple_new = apply_deposit(tuple(new_bp), s.delivered)
        new_bp = list(bp_after)
        new_deliv = {
            RES_STONE:  delivered_tuple_new[0],
            RES_IRON:   delivered_tuple_new[1],
            RES_CRYSTAL:delivered_tuple_new[2],
        }

    # 4) Recogida automática si hay recurso en dest, no está consumido y hay espacio
    tile = grid.resource_at(dest)
    if tile is not None:
        already_taken = (new_mask >> tile.idx) & 1
        if not already_taken and len(new_bp) < CAPACITY:
            new_bp.append(tile.kind)
            new_mask |= (1 << tile.idx)
        # Nota: si la mochila está llena, NO se recoge y el recurso sigue disponible
        # (otra ruta futura podría ir a por él).

    # 5) Construir el nuevo estado inmutable (ordenamos mochila para clave estable)
    s2 = State(
        pos=dest,
        backpack=backpack_tuple(new_bp),
        delivered=(new_deliv[RES_STONE], new_deliv[RES_IRON], new_deliv[RES_CRYSTAL]),
        consumed_mask=new_mask
    )
    return s2, step_cost

def successors(grid: Grid, s: State) -> List[Tuple[State, int]]:
    """
    Genera TODOS los sucesores válidos de s (hasta 4), aplicando step_transition a cada vecino.
    Devuelve lista de (estado_nuevo, costo_del_paso).
    """
    succ: List[Tuple[State, int]] = []
    r, c = s.pos
    for dr, dc in ACTIONS:
        dest = (r + dr, c + dc)
        tr = step_transition(grid, s, dest)
        if tr is not None:
            succ.append(tr)
    return succ
