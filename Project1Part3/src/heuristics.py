# heuristics.py
from typing import Optional
from state import GameState, A_BASE, B_BASE
from rules import manhattan
from grid import LootTile

def _nearest_remaining_resource_dist(state: GameState, pos) -> Optional[int]:
    """Distancia Manhattan al recurso restante más cercano (si no hay, None)."""
    dmin = None
    for tile in state.grid.resources:
        if tile.idx in state.collected_mask:
            continue
        d = manhattan(pos, tile.pos) * state.grid.cheapest_step()
        dmin = d if dmin is None else min(dmin, d)
    return dmin

def evaluate(state: GameState) -> int:
    """
    Heurística sencilla pero efectiva:
    (entregados + mochila)A - (entregados + mochila)B
    - distancia al recurso más cercano (premiamos estar cerca)
    - si lleva recursos: premiamos estar cerca de base
    """
    A = state.A; B = state.B
    baseA = A_BASE; baseB = B_BASE

    scoreA = A.delivered_total + A.bag.count()
    scoreB = B.delivered_total + B.bag.count()
    val = (scoreA - scoreB) * 100  # peso principal

    # Cercanía a recursos
    dA = _nearest_remaining_resource_dist(state, A.pos)
    dB = _nearest_remaining_resource_dist(state, B.pos)
    if dA is not None: val += max(0, 30 - dA)  # acercarse suma
    if dB is not None: val -= max(0, 30 - dB)  # rival cerca resta

    # Si llevan recursos, acercarse a la base es bueno
    if A.bag.count() > 0:
        val += max(0, 30 - manhattan(A.pos, baseA)*state.grid.cheapest_step())
    if B.bag.count() > 0:
        val -= max(0, 30 - manhattan(B.pos, baseB)*state.grid.cheapest_step())

    return val
