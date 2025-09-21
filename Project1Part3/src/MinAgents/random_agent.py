# agents/random_agent.py
import random
from typing import Optional, Tuple
from state import GameState
from rules import legal_moves

class RandomAgent:
    def select_move(self, state: GameState) -> Optional[Tuple[int, int]]:
        moves = legal_moves(state)
        return random.choice(moves) if moves else None
