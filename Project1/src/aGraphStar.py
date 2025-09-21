"""
A* search (reopening-friendly) with a single heuristic.
This variant:
- renames internals,
- tweaks the heap tuple layout,
- and rewrites loops & path rebuild,
while preserving the exact external behavior.
"""

import heapq
from time import perf_counter
from typing import Dict, Tuple, List, Optional

from grid import Grid
from state import State, make_start_state
from moves import expand
from heuristic import heuristic as default_heuristic  # single admissible heuristic


# --------- internal helpers ------------------------------------------------------

def _pack_key(s: State) -> Tuple:
    """
    Compact, comparable key for dicts/sets/heap entries.
    Uniquely identifies a search state.
    """
    return (s.pos, s.backpack, s.delivered, s.consumed_mask)


def _unwind_path(parents: Dict[Tuple, Tuple],
                 archive: Dict[Tuple, State],
                 tip: Tuple) -> List[Tuple[int, int]]:
    """
    Rebuild a path of coordinates [(r,c), ...] from 'tip' back to start
    using the 'parents' map. Stops when a node has no parent (the start).
    """
    seq: List[Tuple[int, int]] = []
    cur = tip
    while True:
        st = archive[cur]
        seq.append(st.pos)
        parent = parents.get(cur)
        if parent is None:
            break
        cur = parent
    seq.reverse()
    return seq


# --------- public solver ---------------------------------------------------------

def astar_solve(grid, heuristic_fn = None):
    """
    A* with lazy reopening (no explicit closed set) and stale-entry skipping.
    Returns a dict with:
      - solved: bool
      - path: List[(r,c)]
      - total_cost: int
      - expanded: int
      - time_ms: float
      - final_state: State
    """
    # Heuristic function alias (readable)
    h_fn = heuristic_fn or default_heuristic

    # Seed node
    start = make_start_state()
    k0 = _pack_key(start)

    # Priority queue entries: (f, seq, g, key)
    # - f = g + h
    # - seq is a monotonically increasing tie-breaker to stabilize the heap
    # - g is included to detect stale entries quickly
    fringe: List[Tuple[int, int, int, Tuple]] = []
    seq = 0

    best_g: Dict[Tuple, int] = {k0: 0}
    parent_of: Dict[Tuple, Tuple] = {}
    archive: Dict[Tuple, State] = {k0: start}
    expanded = 0

    # Push start
    h0 = h_fn(grid, start)
    heapq.heappush(fringe, (h0, seq, 0, k0))
    seq += 1

    # Search loop
    began = perf_counter()
    goal_k: Optional[Tuple] = None
    goal_state: Optional[State] = None

    while fringe:
        f, _, g, key = heapq.heappop(fringe)

        # Skip outdated entries (a better g for this key was seen later)
        if g != best_g.get(key, float("inf")):
            continue

        s = archive[key]

        # Goal test
        if s.is_goal():
            goal_k = key
            goal_state = s
            break

        expanded += 1

        # Generate expand (up to 4 moves)
        for nxt, step in expand(grid, s):
            k2 = _pack_key(nxt)
            g2 = g + step

            # Only keep strictly better paths
            if g2 < best_g.get(k2, float("inf")):
                best_g[k2] = g2
                archive[k2] = nxt
                parent_of[k2] = key

                h2 = h_fn(grid, nxt)
                f2 = g2 + h2
                heapq.heappush(fringe, (f2, seq, g2, k2))
                seq += 1

    ended = perf_counter()

    # Report
    if goal_k is None or goal_state is None:
        return {
            "solved": False,
            "expanded": expanded,
            "time_ms": (ended - began) * 1000.0,
        }

    path = _unwind_path(parent_of, archive, goal_k)
    total_cost = best_g[goal_k]
    return {
        "solved": True,
        "path": path,
        "total_cost": total_cost,
        "expanded": expanded,
        "time_ms": (ended - began) * 1000.0,
        "final_state": goal_state,
    }
