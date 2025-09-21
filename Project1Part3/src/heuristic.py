from typing import Optional
from status import GameState, A_BASE, B_BASE
from conditions import manDist

STEP_PENALTY = 3
NEAR_RES_PLUS= 60
RETURN_BASE_PLUS = 260
POSSESSION_W = 220



def __closest_remaining_cost(state: GameState, pos) -> Optional[int]:
    """Return min(manDist*cheapest_step)s"""
    cheapest = state.grid.cheapest_step()
    # Build all distances to resources that are still on the board
    dists = [
        manDist(pos, tile.pos) * cheapest
        for tile in state.grid.resources
        if tile.idx not in state.collected_mask
    ]
    return min(dists) if dists else None


def __possession_delta(state: GameState) -> int:
    """(A delivered + bag) - (B delivered + bag)"""
    A, B = state.A, state.B
    return (A.delivered_total + A.bag.count()) - (B.delivered_total + B.bag.count())


def __home_pull(state: GameState, pos, base, carrying_count: int) -> int:
    """
    Bonus that pushes the carrier toward its base when carrying anything.
    max(0, RETURN_BASE_PLUS - manDist(pos, base) * cheapest * 10)
    """
    if carrying_count <= 0:
        return 0
    cheapest = state.grid.cheapest_step()
    dist_term = manDist(pos, base) * cheapest * 10
    boost = RETURN_BASE_PLUS - dist_term
    return boost if boost > 0 else 0


def __proximity_term(closest_cost: Optional[int]) -> int:
    if closest_cost is None:
        return 0
    remaining = NEAR_RES_PLUS- closest_cost
    return remaining if remaining > 0 else 0


# ===================== public API =====================

def evaluate(state: GameState) -> int:
    """
    Heuristic:
      + Strong possession (delivered + in bag)
      + Near resource encouragement when resources remain
      + Strong return to base pull when carrying
      - Small per step tax to discourage stalling
    """
    A, B = state.A, state.B

    # 1) Possession (A - B) * weight
    score = __possession_delta(state) * POSSESSION_W

    # 2) Proximity to remaining resources
    a_near = __closest_remaining_cost(state, A.pos)
    b_near = __closest_remaining_cost(state, B.pos)
    score += __proximity_term(a_near)
    score -= __proximity_term(b_near)

    # 3) Return to base pull when carrying items
    score += __home_pull(state, A.pos, A_BASE, A.bag.count())
    score -= __home_pull(state, B.pos, B_BASE, B.bag.count())

    # 4) Per step tax 
    score -= STEP_PENALTY

    return score
