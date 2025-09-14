# file: heuristics.py
from typing import Optional
from grid import Grid, CAPACITY, RES_STONE, RES_IRON, RES_CRYSTAL
from state import State

# -----------------------------
# Utilidad: distancia Manhattan
# -----------------------------
def manhattan(a, b) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


# -----------------------------------------------
# Helpers internos para distancias "a lo necesario"
# -----------------------------------------------
def _nearest_needed_resource_distance_from_pos(grid: Grid, st: State) -> Optional[int]:
    """
    Distancia Manhattan desde la posición ACTUAL del agente (st.pos)
    al recurso más cercano que TODAVÍA NECESITA RECOGER (más allá de lo que ya trae en mochila),
    y que NO haya sido consumido (bitmask).
    Si no hay nada que recolectar, devuelve None.
    """
    need_collect = st.need_to_collect_counts()
    needed_types = {k for k, v in need_collect.items() if v > 0}
    if not needed_types:
        return None

    best = None
    for tile in grid.resources:
        if tile.kind not in needed_types:
            continue
        # ¿ya fue recogido este tile en esta "historia"?
        if (st.consumed_mask >> tile.idx) & 1:
            continue
        d = manhattan(st.pos, tile.pos)
        if best is None or d < best:
            best = d
    return best


def _nearest_needed_resource_distance_from_base(grid: Grid, st: State) -> Optional[int]:
    """
    Distancia Manhattan desde la BASE al recurso necesario más cercano
    (considera lo que falta ENTREGAR; ignora mochila en mano).
    Si no hay necesarios, devuelve None.
    """
    rem = st.remaining_needed()  # lo que falta ENTREGAR (sin aplicar mochila)
    needed_types = {k for k, v in rem.items() if v > 0}
    if not needed_types:
        return None

    best = None
    for tile in grid.resources:
        if tile.kind not in needed_types:
            continue
        if (st.consumed_mask >> tile.idx) & 1:
            continue
        d = manhattan(grid.base, tile.pos)
        if best is None or d < best:
            best = d
    return best


# -----------------------------
# Heurística h1 (básica)
# -----------------------------
def h1(grid: Grid, st: State) -> int:
    """
    Admisible y simple:
    - Si la MOCHILA está LLENA -> distancia a la BASE * costo_mínimo_terreno.
    - Si aún NECESITAS RECOGER -> distancia al recurso necesario más cercano * costo_mínimo.
    - Si ya no necesitas recoger PERO llevas items -> distancia a BASE * costo_mínimo.
    - Si no hay nada que hacer -> 0.

    Usamos costo mínimo de terreno para mantener la subestimación (admisible).
    """
    min_cost = grid.min_terrain_cost()
    total_in_bp = st.total_backpack()

    # 1) mochila llena -> toca ir a base sí o sí
    if total_in_bp == CAPACITY:
        return manhattan(st.pos, grid.base) * min_cost

    # 2) falta recolectar algo (descontando lo que ya llevo)
    need_collect = st.need_to_collect_counts()
    if (need_collect[RES_STONE] + need_collect[RES_IRON] + need_collect[RES_CRYSTAL]) > 0:
        d = _nearest_needed_resource_distance_from_pos(grid, st)
        if d is None:
            # por seguridad: si no encuentra (raro), al menos volver a base
            return manhattan(st.pos, grid.base) * min_cost
        return d * min_cost

    # 3) no falta recolectar pero llevo items -> solo falta ENTREGAR
    if total_in_bp > 0:
        return manhattan(st.pos, grid.base) * min_cost

    # 4) nada pendiente
    return 0


# --------------------------------
# Heurística h_trips (cota de viajes)
# --------------------------------
def h_trips(grid: Grid, st: State) -> int:
    """
    Cota inferior basada en "viajes" mínimos restantes con capacidad=2.

    Idea:
    - R = total que falta ENTREGAR (ignora mochila en mano)
    - carried = lo que llevo en mochila ahora
    - faltante_no_en_mochila = max(0, R - carried)
    - trips = ceil(faltante_no_en_mochila / CAPACITY)
    - costo mínimo por viaje >= 2 * (dist BASE<->recurso necesario más cercano) * (costo_terreno_mínimo)
    - h_trips = trips * costo_minimo_por_viaje

    Es admisible porque:
    - usa la distancia al recurso más cercano (optimista)
    - usa el costo de terreno MÍNIMO (optimista)
    - asume ida y vuelta "perfectas" sin obstáculos (optimista)
    """
    min_cost = grid.min_terrain_cost()

    # R: lo que falta ENTREGAR (sin aplicar mochila)
    rem = st.remaining_needed()
    R = rem[RES_STONE] + rem[RES_IRON] + rem[RES_CRYSTAL]

    carried = st.total_backpack()
    remaining_not_in_bp = max(0, R - carried)
    if remaining_not_in_bp <= 0:
        return 0

    # viajes mínimos necesarios con capacidad=2
    trips = (remaining_not_in_bp + CAPACITY - 1) // CAPACITY  # ceil

    base_to_nearest = _nearest_needed_resource_distance_from_base(grid, st)
    if base_to_nearest is None:
        # Si no hay necesarios, no hay viajes (o ya todo se entrega con lo que llevas)
        return 0

    per_trip = 2 * base_to_nearest * min_cost  # ida y vuelta mínima
    return trips * per_trip


# -----------------------------
# Heurística h3 (recomendada)
# -----------------------------
def h3(grid: Grid, st: State) -> int:
    """
    Tomamos el MÁXIMO entre h1 y h_trips.
    El máximo de cotas inferiores sigue siendo admisible y suele guiar mejor.
    """
    return max(h1(grid, st), h_trips(grid, st))


# Tabla para seleccionar heurística por nombre desde el runner/A*
HEURISTICS = {
    "h1": h1,
    "h_trips": h_trips,
    "h3": h3,
}
