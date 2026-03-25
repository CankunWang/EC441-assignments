from __future__ import annotations

import argparse
import heapq
import json
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


Router = str
Cost = int
Adjacency = Dict[Router, Dict[Router, Cost]]
Links = List[Tuple[Router, Router, Cost]]


BASELINE_LINKS: Links = [
    ("A", "B", 4),
    ("A", "C", 2),
    ("B", "C", 1),
    ("B", "D", 5),
    ("C", "D", 8),
    ("C", "E", 10),
    ("D", "E", 2),
    ("D", "F", 6),
    ("E", "F", 2),
]


def build_graph(links: Iterable[Tuple[Router, Router, Cost]]) -> Adjacency:
    graph: Adjacency = {}
    for left, right, cost in links:
        graph.setdefault(left, {})[right] = cost
        graph.setdefault(right, {})[left] = cost
    return {node: dict(sorted(neighbors.items())) for node, neighbors in sorted(graph.items())}


def generate_lsas(graph: Adjacency) -> Dict[Router, List[Dict[str, int | str]]]:
    lsas: Dict[Router, List[Dict[str, int | str]]] = {}
    for router, neighbors in graph.items():
        lsas[router] = [
            {"neighbor": neighbor, "cost": cost}
            for neighbor, cost in sorted(neighbors.items())
        ]
    return lsas


def flood_lsas(lsas: Dict[Router, List[Dict[str, int | str]]]) -> Dict[Router, Dict[Router, List[Dict[str, int | str]]]]:
    return {router: lsas for router in sorted(lsas)}


def rebuild_graph_from_lsdb(lsdb: Dict[Router, List[Dict[str, int | str]]]) -> Adjacency:
    links: Links = []
    seen = set()
    for router, entries in sorted(lsdb.items()):
        for entry in entries:
            neighbor = str(entry["neighbor"])
            cost = int(entry["cost"])
            edge_key = tuple(sorted((router, neighbor)))
            if edge_key in seen:
                continue
            seen.add(edge_key)
            links.append((router, neighbor, cost))
    return build_graph(links)


def dijkstra(graph: Adjacency, source: Router) -> Tuple[Dict[Router, float], Dict[Router, Optional[Router]]]:
    distances = {node: float("inf") for node in graph}
    predecessors: Dict[Router, Optional[Router]] = {node: None for node in graph}
    distances[source] = 0

    queue: List[Tuple[float, Router]] = [(0, source)]
    visited = set()

    while queue:
        current_distance, node = heapq.heappop(queue)
        if node in visited:
            continue
        visited.add(node)

        for neighbor, cost in sorted(graph[node].items()):
            candidate_distance = current_distance + cost
            if candidate_distance < distances[neighbor]:
                distances[neighbor] = candidate_distance
                predecessors[neighbor] = node
                heapq.heappush(queue, (candidate_distance, neighbor))

    return distances, predecessors


def reconstruct_path(predecessors: Dict[Router, Optional[Router]], source: Router, destination: Router) -> List[Router]:
    if source == destination:
        return [source]

    path: List[Router] = []
    current: Optional[Router] = destination
    while current is not None:
        path.append(current)
        if current == source:
            break
        current = predecessors[current]

    if not path or path[-1] != source:
        return []

    return list(reversed(path))


def build_forwarding_table(graph: Adjacency, source: Router) -> Dict[Router, Dict[str, object]]:
    distances, predecessors = dijkstra(graph, source)
    table: Dict[Router, Dict[str, object]] = {}

    for destination in sorted(graph):
        if destination == source:
            continue

        path = reconstruct_path(predecessors, source, destination)
        if not path:
            table[destination] = {"next_hop": None, "cost": None, "path": []}
            continue

        next_hop = path[1] if len(path) > 1 else destination
        table[destination] = {
            "next_hop": next_hop,
            "cost": int(distances[destination]),
            "path": path,
        }

    return table


def build_shortest_path_tree(graph: Adjacency, source: Router) -> List[Dict[str, object]]:
    distances, predecessors = dijkstra(graph, source)
    edges = []
    for node in sorted(graph):
        if node == source:
            continue
        predecessor = predecessors[node]
        if predecessor is None:
            continue
        edges.append(
            {
                "from": predecessor,
                "to": node,
                "cost": graph[predecessor][node],
                "distance_from_source": int(distances[node]),
            }
        )
    return edges


def forwarding_tables_for_all_routers(graph: Adjacency) -> Dict[Router, Dict[Router, Dict[str, object]]]:
    return {router: build_forwarding_table(graph, router) for router in sorted(graph)}


def count_changed_routes(
    before: Dict[Router, Dict[str, object]],
    after: Dict[Router, Dict[str, object]],
) -> int:
    changed = 0
    for destination in sorted(before):
        if before[destination]["next_hop"] != after[destination]["next_hop"]:
            changed += 1
    return changed


def format_table(title: str, table: Dict[Router, Dict[str, object]]) -> str:
    lines = [title, "-" * len(title), f"{'Destination':<12}{'Next Hop':<12}{'Cost':<8}Path"]
    for destination, entry in sorted(table.items()):
        path = " -> ".join(entry["path"]) if entry["path"] else "unreachable"
        next_hop = entry["next_hop"] if entry["next_hop"] is not None else "-"
        cost = entry["cost"] if entry["cost"] is not None else "-"
        lines.append(f"{destination:<12}{str(next_hop):<12}{str(cost):<8}{path}")
    return "\n".join(lines)


def scenario_summary(name: str, graph: Adjacency, source: Router, description: str) -> Dict[str, object]:
    lsas = generate_lsas(graph)
    flooded = flood_lsas(lsas)
    lsdb_consistent = all(database == lsas for database in flooded.values())
    rebuilt_graphs = {router: rebuild_graph_from_lsdb(database) for router, database in flooded.items()}
    reconstruction_consistent = all(rebuilt == graph for rebuilt in rebuilt_graphs.values())

    return {
        "scenario": name,
        "description": description,
        "graph": graph,
        "lsas": lsas,
        "lsdb_consistent_across_routers": lsdb_consistent,
        "topology_reconstruction_matches_original": reconstruction_consistent,
        "source_router": source,
        "shortest_path_tree": build_shortest_path_tree(graph, source),
        "forwarding_tables": forwarding_tables_for_all_routers(graph),
        "source_forwarding_table": build_forwarding_table(graph, source),
    }


def write_outputs(output_dir: Path, summaries: List[Dict[str, object]], source: Router) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    results_path = output_dir / "simulation_results.json"
    results_path.write_text(json.dumps({"source_router": source, "scenarios": summaries}, indent=2), encoding="utf-8")

    baseline = summaries[0]["source_forwarding_table"]
    failure = summaries[1]["source_forwarding_table"]
    cost_change = summaries[2]["source_forwarding_table"]

    comparison_lines = [
        format_table("Baseline forwarding table for router A", baseline),
        "",
        format_table("After link failure (B-C removed)", failure),
        "",
        format_table("After cost change (A-B reduced from 4 to 1)", cost_change),
        "",
        "Route changes from baseline:",
        f"- Link failure changed next hops for {count_changed_routes(baseline, failure)} destinations.",
        f"- Cost change changed next hops for {count_changed_routes(baseline, cost_change)} destinations.",
    ]
    (output_dir / "router_A_tables.txt").write_text("\n".join(comparison_lines), encoding="utf-8")


def build_scenarios(source: Router) -> List[Dict[str, object]]:
    baseline_graph = build_graph(BASELINE_LINKS)

    failed_links = [link for link in BASELINE_LINKS if tuple(sorted(link[:2])) != ("B", "C")]
    failure_graph = build_graph(failed_links)

    changed_links: Links = []
    for left, right, cost in BASELINE_LINKS:
        if tuple(sorted((left, right))) == ("A", "B"):
            changed_links.append((left, right, 1))
        else:
            changed_links.append((left, right, cost))
    cost_change_graph = build_graph(changed_links)

    return [
        scenario_summary(
            name="baseline",
            graph=baseline_graph,
            source=source,
            description="Initial topology with six routers and weighted links.",
        ),
        scenario_summary(
            name="link_failure",
            graph=failure_graph,
            source=source,
            description="Link B-C fails, forcing routers to recompute shortest paths.",
        ),
        scenario_summary(
            name="cost_change",
            graph=cost_change_graph,
            source=source,
            description="Link A-B cost drops from 4 to 1, making the A-B corridor more attractive.",
        ),
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate link-state routing with Dijkstra-based forwarding.")
    parser.add_argument(
        "--source",
        default="A",
        help="Source router used for shortest-path tree and comparison tables.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(Path(__file__).with_name("outputs")),
        help="Directory for generated JSON and text outputs.",
    )
    args = parser.parse_args()

    summaries = build_scenarios(args.source)
    write_outputs(Path(args.output_dir), summaries, args.source)

    print("Generated scenarios:")
    for summary in summaries:
        print(f"- {summary['scenario']}: {summary['description']}")
    print(f"Outputs written to: {Path(args.output_dir).resolve()}")


if __name__ == "__main__":
    main()
