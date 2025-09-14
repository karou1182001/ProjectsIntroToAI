# file: astar.py
import heapq
from time import perf_counter
from typing import Dict, Tuple, List, Optional

from grid import Grid
from state import State, make_start_state
from transitions import successors
from heuristics import HEURISTICS

def state_key(s: State) -> Tuple:
    """Clave única/estable para sets/dicts/cola."""
    return (s.pos, s.backpack, s.delivered, s.consumed_mask)

def reconstruct_path(came_from: Dict[Tuple, Tuple],
                     key_to_state: Dict[Tuple, State],
                     goal_key: Tuple) -> List[Tuple[int, int]]:
    """Reconstruye la ruta [(r,c), ...] del inicio a la meta."""
    path: List[Tuple[int, int]] = []
    k = goal_key
    while k in came_from:
        st = key_to_state[k]
        path.append(st.pos)
        k = came_from[k]  # padre
    st0 = key_to_state[k]
    path.append(st0.pos)
    path.reverse()
    return path

def astar_solve(grid: Grid, heuristic_name: str = "h3") -> Dict:
    """
    A* con "reaperturas" (sin closed set) y descarte de entradas obsoletas.
    Retorna:
      solved, path, total_cost, expanded, time_ms, final_state
    """
    h_fn = HEURISTICS[heuristic_name]

    start = make_start_state()
    start_k = state_key(start)

    # Cola: (f, h, -g, tie, key)
    open_heap: List[Tuple[int, int, int, int, Tuple]] = []
    tiebreak = 0

    g_cost: Dict[Tuple, int] = {start_k: 0}
    came_from: Dict[Tuple, Tuple] = {}
    key_to_state: Dict[Tuple, State] = {start_k: start}
    expanded = 0

    h0 = h_fn(grid, start)
    heapq.heappush(open_heap, (h0, h0, 0, tiebreak, start_k))
    tiebreak += 1

    t0 = perf_counter()
    goal_key: Optional[Tuple] = None
    goal_state: Optional[State] = None

    while open_heap:
        f, h, neg_g, _, key = heapq.heappop(open_heap)

        # DESCARTE de entradas obsoletas:
        # si el g que sale de la cola NO coincide con el mejor g conocido, ignora
        if -neg_g != g_cost.get(key, float("inf")):
            continue

        s = key_to_state[key]
        g = -neg_g

        # ¿Meta?
        if s.is_goal():
            goal_key = key
            goal_state = s
            break

        expanded += 1

        # Expansión (hasta 4)
        for s2, step_cost in successors(grid, s):
            k2 = state_key(s2)
            new_g = g + step_cost

            # Dominancia: solo si mejora g
            if new_g < g_cost.get(k2, float("inf")):
                g_cost[k2] = new_g
                key_to_state[k2] = s2
                came_from[k2] = key

                h2 = h_fn(grid, s2)
                f2 = new_g + h2
                heapq.heappush(open_heap, (f2, h2, -new_g, tiebreak, k2))
                tiebreak += 1

    t1 = perf_counter()

    if goal_key is None or goal_state is None:
        return {
            "solved": False,
            "expanded": expanded,
            "time_ms": (t1 - t0) * 1000.0,
        }

    path = reconstruct_path(came_from, key_to_state, goal_key)
    total_cost = g_cost[goal_key]
    return {
        "solved": True,
        "path": path,
        "total_cost": total_cost,
        "expanded": expanded,
        "time_ms": (t1 - t0) * 1000.0,
        "final_state": goal_state,
    }
