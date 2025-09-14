# file: state.py
from dataclasses import dataclass
from typing import Tuple, Dict, List
from grid import (
    Coord,
    RES_STONE, RES_IRON, RES_CRYSTAL,
    REQ_COUNTS, CAPACITY
)

# ---------------------------------------------------------
# Helpers para normalizar y representar entregas/mochila
# ---------------------------------------------------------

def clamp_delivered(d: Dict[str, int]) -> Dict[str, int]:
    """
    Limita las cantidades entregadas a los máximos requeridos (3/2/1).
    Esto normaliza el espacio de estados y evita contar de más.
    """
    return {
        RES_STONE:  min(d.get(RES_STONE, 0),  REQ_COUNTS[RES_STONE]),
        RES_IRON:   min(d.get(RES_IRON, 0),   REQ_COUNTS[RES_IRON]),
        RES_CRYSTAL:min(d.get(RES_CRYSTAL, 0),REQ_COUNTS[RES_CRYSTAL]),
    }

def delivered_tuple(d: Dict[str, int]) -> Tuple[int, int, int]:
    """
    Convierte un dict de entregas a una tupla fija (stone, iron, crystal),
    siempre después de hacer clamp.
    """
    c = clamp_delivered(d)
    return (c[RES_STONE], c[RES_IRON], c[RES_CRYSTAL])

def backpack_tuple(items: List[str]) -> Tuple[str, ...]:
    """
    Devuelve la mochila como una TUPLA ORDENADA (hashable).
    Ordenar es clave para que ('IRON','STONE') == ('STONE','IRON') a nivel de clave.
    """
    return tuple(sorted(items))


# ---------------------------------------------------------
# Estado principal que A* va a explorar
# ---------------------------------------------------------
@dataclass(frozen=True)
class State:
    pos: Coord                         # posición del agente (r,c)
    backpack: Tuple[str, ...]          # tupla ordenada de recursos; len <= CAPACITY
    delivered: Tuple[int, int, int]    # (stone, iron, crystal) ENTREGADOS en base
    consumed_mask: int                 # bitmask de recursos YA recogidos (por índice de tile)

    # ---------- Consultas de alto nivel ----------
    def is_goal(self) -> bool:
        """¿Ya alcanzamos la meta 3/2/1 entregados?"""
        return self.delivered == (
            REQ_COUNTS[RES_STONE],
            REQ_COUNTS[RES_IRON],
            REQ_COUNTS[RES_CRYSTAL],
        )

    def total_backpack(self) -> int:
        """Cuántos items llevo en total (capacidad máxima = CAPACITY)."""
        return len(self.backpack)

    def count_in_backpack(self, kind: str) -> int:
        """Cuántos items de un TIPO específico llevo en la mochila."""
        return sum(1 for x in self.backpack if x == kind)

    def delivered_as_dict(self) -> Dict[str, int]:
        """Entregas en dict (útil para cálculos intermedios)."""
        return {
            RES_STONE:  self.delivered[0],
            RES_IRON:   self.delivered[1],
            RES_CRYSTAL:self.delivered[2],
        }

    def remaining_needed(self) -> Dict[str, int]:
        """
        Cuánto FALTA por ENTREGAR todavía (sin considerar lo que ya llevo en la mochila).
        """
        d = self.delivered_as_dict()
        return {
            RES_STONE:  max(0, REQ_COUNTS[RES_STONE]  - d[RES_STONE]),
            RES_IRON:   max(0, REQ_COUNTS[RES_IRON]   - d[RES_IRON]),
            RES_CRYSTAL:max(0, REQ_COUNTS[RES_CRYSTAL]- d[RES_CRYSTAL]),
        }

    def need_to_collect_counts(self) -> Dict[str, int]:
        """
        Cuánto me falta RECOGER (no solo entregar), descontando lo que YA llevo en la mochila.
        (Clampeado a 0).
        """
        rem = self.remaining_needed()
        return {
            RES_STONE:  max(0, rem[RES_STONE]   - self.count_in_backpack(RES_STONE)),
            RES_IRON:   max(0, rem[RES_IRON]    - self.count_in_backpack(RES_IRON)),
            RES_CRYSTAL:max(0, rem[RES_CRYSTAL] - self.count_in_backpack(RES_CRYSTAL)),
        }


# ---------------------------------------------------------
# Otras utilidades comunes en la transición/A*
# ---------------------------------------------------------

def apply_deposit(backpack: Tuple[str, ...],
                  delivered: Tuple[int, int, int]) -> Tuple[Tuple[str, ...], Tuple[int, int, int]]:
    """
    Simula el depósito automático en la BASE:
    - Suma el contenido de la mochila a 'delivered'
    - Hace clamp a 3/2/1
    - Devuelve mochila vacía y la tupla entregada actualizada
    """
    d = {
        RES_STONE:  delivered[0],
        RES_IRON:   delivered[1],
        RES_CRYSTAL:delivered[2],
    }
    for item in backpack:
        d[item] = d.get(item, 0) + 1
    d = clamp_delivered(d)
    return (), (d[RES_STONE], d[RES_IRON], d[RES_CRYSTAL])

def make_start_state() -> State:
    """
    Estado inicial: en (0,0), mochila vacía, nada entregado, sin recursos consumidos.
    """
    return State(
        pos=(0, 0),
        backpack=(),
        delivered=(0, 0, 0),
        consumed_mask=0
    )
