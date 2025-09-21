# heuristics.py
from typing import Optional
from status import GameState, A_BASE, B_BASE
from conditions import manDist

STEP_TAX = 3            # “impuesto por paso”: rompe empates y castiga paseos
NEAR_RES_BONUS = 60     # cuánta recompensa por estar cerca de recurso
RETURN_BASE_BONUS = 260 # fuerza a volver a base si lleva ítems
POSSESSION_W = 220      # peso de (entregas + mochila)

def _nearest_remaining_resource_dist(state: GameState, pos) -> Optional[int]:
    dmin = None
    for tile in state.grid.resources:
        if tile.idx in state.collected_mask:
            continue
        d = manDist(pos, tile.pos) * state.grid.cheapest_step()
        dmin = d if dmin is None else min(dmin, d)
    return dmin

def evaluate(state: GameState) -> int:
    A, B = state.A, state.B
    baseA, baseB = A_BASE, B_BASE

    # 1) Posesión fuerte: entregado + mochila (A menos B)
    val = (A.delivered_total + A.bag.count()
           - (B.delivered_total + B.bag.count())) * POSSESSION_W

    # 2) Proximidad a recursos si aún quedan
    dA = _nearest_remaining_resource_dist(state, A.pos)
    dB = _nearest_remaining_resource_dist(state, B.pos)
    if dA is not None: val += max(0, NEAR_RES_BONUS - dA)
    if dB is not None: val -= max(0, NEAR_RES_BONUS - dB)

    # 3) Si llevan recursos, empujar fuerte hacia su base
    if A.bag.count() > 0:
        val += max(0, RETURN_BASE_BONUS - manDist(A.pos, baseA) * state.grid.cheapest_step() * 10)
    if B.bag.count() > 0:
        val -= max(0, RETURN_BASE_BONUS - manDist(B.pos, baseB) * state.grid.cheapest_step() * 10)

    # 4) Impuesto por paso: favorece terminar y evita ping-pong
    val -= STEP_TAX

    return val
