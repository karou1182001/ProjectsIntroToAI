# agents/minimax_agent.py
from typing import Tuple, Optional
from state import GameState
from rules import legal_moves, apply_move
from heuristics import evaluate

class MinimaxAgent:
    def __init__(self, depth: int = 4):
        self.depth = depth

    def select_move(self, state: GameState) -> Optional[Tuple[int, int]]:
        best_val = None
        best_mv = None
        alpha = -10**9
        beta  =  10**9
        for mv in legal_moves(state):
            child = apply_move(state, mv)
            val = self._minimax(child, self.depth-1, alpha, beta)
            # Si soy A (max) en este estado, el valor que vuelve es
            # con respecto a utilidad A-B (convención de evaluate + utility)
            if best_val is None or val > best_val:
                best_val = val
                best_mv = mv
            alpha = max(alpha, val)
            if beta <= alpha:
                break
        return best_mv

    def _minimax(self, state: GameState, depth: int, alpha: int, beta: int) -> int:
        if state.is_terminal() or depth == 0:
            # usar utility si terminal; si no, heurística
            return state.utility() * 1000 if state.is_terminal() else evaluate(state)

        # El “max” es el jugador A cuando es su turno; el “min” es B en su turno
        is_max = (state.turn == "A")
        if is_max:
            value = -10**9
            for mv in legal_moves(state):
                value = max(value, self._minimax(apply_move(state, mv), depth-1, alpha, beta))
                alpha = max(alpha, value)
                if beta <= alpha:
                    break
            return value
        else:
            value = 10**9
            for mv in legal_moves(state):
                value = min(value, self._minimax(apply_move(state, mv), depth-1, alpha, beta))
                beta = min(beta, value)
                if beta <= alpha:
                    break
            return value
