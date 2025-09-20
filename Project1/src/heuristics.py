# file: heuristics.py
from grid import Grid, CAPACITY, RES_STONE, RES_IRON, RES_CRYSTAL
from state import State

def manhattan(a, b) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def _nearest_needed_resource_distance_from_pos(grid: Grid, st: State):
    """
    Distance from the agent to the closest not-yet-consumed resource
    that is still needed (considering what’s already delivered and in the backpack).
    Returns None if nothing is needed anymore.
    """
    need_collect = st.need_to_collect_counts()
    needed_types = {k for k, v in need_collect.items() if v > 0}
    if not needed_types:
        return None

    best = None
    for tile in grid.resources:
        if tile.kind not in needed_types:
            continue
        if (st.consumed_mask >> tile.idx) & 1:
            continue
        d = manhattan(st.pos, tile.pos)
        if best is None or d < best:
            best = d
    return best

def h1(grid: Grid, st: State) -> int:
    """
    Admissible heuristic aligned with the assignment examples:

    - If backpack is FULL -> distance to BASE (you must deposit).
    - Else if you still NEED to COLLECT something -> distance to the nearest needed resource.
    - Else if you carry something but don’t need more -> distance to BASE.
    - Else nothing left to do -> 0.

    We multiply Manhattan distance by the MIN terrain cost to stay optimistic (admissible).
    """
    min_cost = grid.min_terrain_cost()
    total_in_bp = st.total_backpack()

    # 1) Full backpack → go to base
    if total_in_bp == CAPACITY:
        return manhattan(st.pos, grid.base) * min_cost

    # 2) Still need to collect (after discounting what’s in the backpack)
    need_collect = st.need_to_collect_counts()
    if (need_collect[RES_STONE] + need_collect[RES_IRON] + need_collect[RES_CRYSTAL]) > 0:
        d = _nearest_needed_resource_distance_from_pos(grid, st)
        return (d or manhattan(st.pos, grid.base)) * min_cost

    # 3) Nothing left to collect, but carrying items → deliver them
    if total_in_bp > 0:
        return manhattan(st.pos, grid.base) * min_cost

    # 4) Goal-ready
    return 0

# Keep a small dispatch for compatibility with astar.py
HEURISTICS = {"h1": h1}
