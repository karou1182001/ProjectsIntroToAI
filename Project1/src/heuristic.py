# file: heuristics.py
from grid import Grid, CAPACITY, RES_STONE, RES_IRON, RES_CRYSTAL
from state import State

def l1(a, b) -> int:
    #mahhatta distance
    return (a[0] - b[0]) if a[0] >= b[0] else (b[0] - a[0])  \
         + (a[1] - b[1]) if a[1] >= b[1] else (b[1] - a[1])

def _closest_missing_resource_steps(grid: Grid, st: State):
    """
    Return the Manhattan steps from the agent to the nearest resource
    that is (a) still needed and (b) not yet consumed in this search branch.
    None if no resources are needed anymore.
    """
    missing = st.need_to_collect_counts()
    want = {k for k, v in missing.items() if v > 0}
    if not want:
        return None

    # Build candidate distances in a single pass, ignore consumed tiles
    candidates = []
    mask = st.consumed_mask
    sr, sc = st.pos
    for t in grid.resources:
        if t.kind in want and not ((mask >> t.idx) & 1):
            # inline L1 to avoid function-call overhead and look different
            dr = sr - t.pos[0] if sr >= t.pos[0] else t.pos[0] - sr
            dc = sc - t.pos[1] if sc >= t.pos[1] else t.pos[1] - sc
            candidates.append(dr + dc)

    return None if not candidates else min(candidates)

def heuristic(grid: Grid, st: State) -> int:
    """
    - If backpack is full -> must return to base (Manhattan to base).
    - Else if we still need to collect -> Manhattan to nearest needed resource.
    - Else if carrying something (but no more needed) -> go to base.
    - Else -> 0.

    Multiply by the minimum terrain-enter cost to remain optimistic.
    """
    step_floor = grid.cheapest_step()

    # Full pack → deposit
    if st.total_backpack() == CAPACITY:
        return l1(st.pos, grid.base) * step_floor

    # Still missing items -> head to the nearest needed resource
    miss = st.need_to_collect_counts()
    if (miss[RES_STONE] + miss[RES_IRON] + miss[RES_CRYSTAL]) > 0:
        d = _closest_missing_resource_steps(grid, st)
        # Fallback to base distance if, for any reason, no target is found
        return (d if d is not None else l1(st.pos, grid.base)) * step_floor

    # Nothing left to collect, but we carry items → deliver
    if st.total_backpack() > 0:
        return l1(st.pos, grid.base) * step_floor

    # Goal-ready
    return 0

# --- add: baseline heuristic for validation (Dijkstra) 
def heuristic_zero(grid, st):
    """Admissible baseline. Always 0 -> A* == Dijkstra (slower, gold standard)."""
    return 0

