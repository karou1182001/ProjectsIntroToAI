import random
from typing import Optional, Tuple
from status import GameState
from conditions import valid_mov

class RandomAgent:
    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed)

    def decide_move(self, state: GameState) -> Optional[Tuple[int, int]]:
        ops = list(valid_mov(state))
        return self.rng.choice(ops) if ops else None
