
from typing import Optional, Tuple, Dict, Iterable
from status import GameState, A_BASE, B_BASE
from conditions import (
    legal_moves,
    apply_move,
    manhattan,
    moves_towards_base_if_full,
)
from heuristic import evaluate
from grid import CAPACITY


# =======================
#  Tunables / constants
# =======================
INF = 10**9
TERMINAL_BOOST = 10**6
LOOP_PENALTY = 150
FALLBACK_DIST = 999  


# ====================================
# Small helpers 
# ====================================
def _currentState(s: GameState) -> Tuple:
    return (s.A.pos, s.B.pos, s.A.bag.items, s.B.bag.items, s.collected_mask, s.turn)


def _closest_obj_dist(s: GameState, pos: Tuple[int, int]) -> Optional[int]:
    best = None
    for t in s.grid.resources:
        if t.idx in s.collected_mask:
            continue
        d = manhattan(pos, t.pos)
        best = d if best is None else min(best, d)
    return best


# =========================
# The Agent 
# =========================
class AlphaBetaAgent:
    def __init__(self, depth: int = 5) -> None:
        self.depth = depth
        self._seen: Dict[Tuple, int] = {}

    def decide_move(self, state: GameState) -> Optional[Tuple[int, int]]:
        """
          * Respect MAX/MIN role at the root
          * Apply bag ull policy at the root
          * Use move ordering and  alpha beta
          * Tie break: when values tie and bag is full, prefer the move that reduces distance to base more
        """
        self._seen.clear()

        is_max = (state.turn == "A")
        a, b = -INF, INF
        best_val = -INF if is_max else INF
        best_move: Optional[Tuple[int, int]] = None

        base = A_BASE if is_max else B_BASE
        for mv in self._root_candidates(state):
            nxt = apply_move(state, mv)
            val = self._alphabeta(nxt, self.depth - 1, a, b)

            if self._is_better(val, best_val, is_max):
                best_val, best_move = val, mv
            elif val == best_val:
                if self._active_bag_count(state) >= CAPACITY:
                    if self._closer(mv, best_move, base):
                        best_val, best_move = val, mv

            if is_max:
                a = max(a, val)
            else:
                b = min(b, val)
            if b <= a:
                break  

        return best_move

    def _alphabeta(self, s: GameState, depth: int, a: int, b: int) -> int:
        """Standard minimax + alpha–beta with repetition penalty and good ordering."""
        key = _currentState(s)
        self._seen[key] = self._seen.get(key, 0) + 1
        rep_count = self._seen[key]


        if s.is_terminal() or depth == 0:
            return self._score_leaf(s, rep_count)

        max_turn = (s.turn == "A")
        if max_turn:
            best = -INF
            for mv in self._ordered_children(s):
                nxt = apply_move(s, mv)
                best = max(best, self._alphabeta(nxt, depth - 1, a, b))
                a = max(a, best)
                if b <= a:
                    break
            return best
        else:
            best = INF
            for mv in self._ordered_children(s):
                nxt = apply_move(s, mv)
                best = min(best, self._alphabeta(nxt, depth - 1, a, b))
                b = min(b, best)
                if b <= a:
                    break
            return best

    def _root_candidates(self, s: GameState) -> Iterable[Tuple[int, int]]:
        moves = moves_towards_base_if_full(s)
        return sorted(moves, key=lambda mv: self._order_key(s, mv))

    def _ordered_children(self, s: GameState) -> Iterable[Tuple[int, int]]:
        moves = moves_towards_base_if_full(s)
        return sorted(moves, key=lambda mv: self._order_key(s, mv))
    
    def _score_leaf(self, s: GameState, repeats: int) -> int:
        if s.is_terminal():
            return s.utility() * TERMINAL_BOOST
        score = evaluate(s)
        if repeats > 1:
            score -= LOOP_PENALTY * (repeats - 1)
        return score

    def _order_key(self, s: GameState, mv: Tuple[int, int]) -> Tuple[int, int]:
        who = s.turn
        base = A_BASE if who == "A" else B_BASE
        bag_ct = self._active_bag_count(s)
        dest = mv

        if bag_ct >= CAPACITY:
            return (0, manhattan(dest, base))
        if bag_ct > 0:
            return (1, manhattan(dest, base))

        d_res = _closest_obj_dist(s, dest)
        return (2, d_res if d_res is not None else FALLBACK_DIST)

    # ---------- 4.5 Tiny helpers (intent-focused) ----------
    @staticmethod
    def _is_better(val: int, best: int, is_max: bool) -> bool:
        return (val > best) if is_max else (val < best)

    @staticmethod
    def _closer(a_move: Tuple[int, int], b_move: Optional[Tuple[int, int]], base: Tuple[int, int]) -> bool:
        if b_move is None:
            return True
        return manhattan(a_move, base) < manhattan(b_move, base)

    @staticmethod
    def _active_bag_count(s: GameState) -> int:
        return s.A.bag.count() if s.turn == "A" else s.B.bag.count()
