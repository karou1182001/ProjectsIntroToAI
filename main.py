# file: main.py
from astar import astar_solve
from maps import build_map_A, build_map_B, build_map_C
from utils import ascii_render, delivered_str

def run_on_map(name: str, grid, heuristic="h3"):
    print("="*70)
    print(f"Map: {name} | Heuristic: {heuristic}")
    print("Grid (terrain/resource overlay):")
    print(ascii_render(grid))
    print("-"*70)

    res = astar_solve(grid, heuristic_name=heuristic)
    if not res["solved"]:
        print("No solution found.")
        print(f"Expanded: {res['expanded']} | Time: {res['time_ms']:.2f} ms")
        return

    print("Solved!\n")
    print("Path:", res["path"])
    print("Total cost:", res["total_cost"])
    print(f"Expanded nodes: {res['expanded']} | Time: {res['time_ms']:.2f} ms")

    final_state = res["final_state"]
    print("Final delivered:", delivered_str(final_state.delivered))

    print("\nGrid with path (*) marked:")
    print(ascii_render(grid, res["path"]))
    print()

if __name__ == "__main__":
    for name, grid in [
        ("A", build_map_A()),
        ("B", build_map_B()),
        ("C", build_map_C()),
    ]:
        for h in ["h1", "h3"]:
            run_on_map(name, grid, heuristic=h)
