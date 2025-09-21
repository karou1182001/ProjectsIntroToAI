# agents/minimax_agent.py
from typing import Optional, Tuple
from state import GameState, A_BASE, B_BASE
from rules import legal_moves, apply_move, manhattan, moves_towards_base_if_full
from heuristics import evaluate
from grid import CAPACITY

INF = 10**9
TERM_MULT = 10**6
REPEAT_PENALTY = 150

def _nearest_remaining_resource_dist(state: GameState, pos):
    dmin = None
    for tile in state.grid.resources:
        if tile.idx in state.collected_mask:
            continue
        d = manhattan(pos, tile.pos)
        dmin = d if dmin is None else min(dmin, d)
    return dmin

def _move_order_key(state: GameState, mv: Tuple[int,int]):
    """Orden: si llevo recursos → acercarme a base; si no → acercarme a recurso."""
    who = state.turn
    base = A_BASE if who == "A" else B_BASE
    # distancia luego de mover
    after = mv
    # si mochila llena, prioriza base fuertemente
    bag_count = (state.A.bag.count() if who == "A" else state.B.bag.count())
    if bag_count >= CAPACITY:
        return (0, manhattan(after, base))
    # si lleva algo (no llena), también prioriza base pero con menos fuerza
    if bag_count > 0:
        return (1, manhattan(after, base))
    # vacía: prioriza estar cerca de algún recurso
    d = _nearest_remaining_resource_dist(state, after)
    return (2, d if d is not None else 999)

def _hashable(s: GameState):
    return (s.A.pos, s.B.pos, s.A.bag.items, s.B.bag.items, s.collected_mask, s.turn)

class MinimaxAgent:
    def __init__(self, depth: int = 5):
        self.depth = depth

    def select_move(self, state: GameState) -> Optional[Tuple[int, int]]:
        self._seen_counts = {}

        root_is_max = (state.turn == "A")
        best_val = -INF if root_is_max else INF
        best_mv = None
        alpha, beta = -INF, INF

        # *** CLAVE: si la mochila del jugador en turno está llena, filtra movimientos hacia base
        root_moves = moves_towards_base_if_full(state)
        moves = sorted(root_moves, key=lambda mv: _move_order_key(state, mv))

        # desempate anti-backtrack: si dos valores empatan, prefiere el que REDUCE distancia a base
        base = A_BASE if state.turn == "A" else B_BASE
        curd = manhattan((state.A.pos if state.turn=="A" else state.B.pos), base)

        for mv in moves:
            child = apply_move(state, mv)
            val = self._minimax(child, self.depth - 1, alpha, beta)

            if best_mv is None:
                best_val, best_mv = val, mv
            else:
                better = (val > best_val) if root_is_max else (val < best_val)
                if better:
                    best_val, best_mv = val, mv
                elif val == best_val:
                    # tie-breaker: preferir movimiento que acerque más a base si mochila llena
                    nextd = manhattan(mv, base)
                    bestd = manhattan(best_mv, base)
                    if nextd < bestd:
                        best_val, best_mv = val, mv

            if root_is_max:
                alpha = max(alpha, val)
            else:
                beta = min(beta, val)

            if beta <= alpha:
                break

        return best_mv

    def _bump_seen(self, s: GameState) -> int:
        h = _hashable(s)
        k = self._seen_counts.get(h, 0) + 1
        self._seen_counts[h] = k
        return k

    def _score_leaf(self, s: GameState, repeated: int) -> int:
        if s.is_terminal():
            return s.utility() * TERM_MULT
        val = evaluate(s)
        if repeated > 1:
            val -= REPEAT_PENALTY * (repeated - 1)
        return val

    def _children(self, s: GameState):
        """En nodos internos, mantiene la política: si mochila llena, restringe a movimientos hacia base."""
        ms = moves_towards_base_if_full(s)
        return sorted(ms, key=lambda mv: _move_order_key(s, mv))

    def _minimax(self, state: GameState, depth: int, alpha: int, beta: int) -> int:
        reps = self._bump_seen(state)
        if state.is_terminal() or depth == 0:
            return self._score_leaf(state, reps)

        is_max = (state.turn == "A")
        if is_max:
            value = -INF
            for mv in self._children(state):
                value = max(value, self._minimax(apply_move(state, mv), depth - 1, alpha, beta))
                alpha = max(alpha, value)
                if beta <= alpha:
                    break
            return value
        else:
            value = INF
            for mv in self._children(state):
                value = min(value, self._minimax(apply_move(state, mv), depth - 1, alpha, beta))
                beta = min(beta, value)
                if beta <= alpha:
                    break
            return value
