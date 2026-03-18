from __future__ import annotations

import statistics
from collections import Counter

from trace_tools import HopResult


def path_signature(hops: list[HopResult]) -> list[str]:
    return [hop.ip if hop.ip else "*" for hop in hops]


def analyze_stability(all_runs: list[list[HopResult]]) -> dict:
    if not all_runs:
        return {}

    max_len = max(len(run) for run in all_runs)
    per_hop_stability = []
    stable_hops = 0
    variable_hops = 0

    for i in range(max_len):
        seen = []
        for run in all_runs:
            if i < len(run):
                seen.append(run[i].ip if run[i].ip else "*")
            else:
                seen.append("*")

        stable = len(set(seen)) == 1
        if stable:
            stable_hops += 1
        else:
            variable_hops += 1

        non_timeout = [ip for ip in seen if ip != "*"]
        per_hop_stability.append(
            {
                "hop": i + 1,
                "observed": seen,
                "majority": Counter(seen).most_common(1)[0][0],
                "unique_non_timeout_ips": sorted(set(non_timeout)),
                "stable_across_runs": stable,
            }
        )

    return {
        "run_count": len(all_runs),
        "stable_hops": stable_hops,
        "variable_hops": variable_hops,
        "per_hop_stability": per_hop_stability,
        "path_signatures": [path_signature(run) for run in all_runs],
    }


def summarize_runs(target: str, destination_ip: str | None, all_runs: list[list[HopResult]]) -> dict:
    latencies = []
    transition_count = 0
    private_hops = 0
    reachable_runs = 0

    for run in all_runs:
        for hop in run:
            if hop.avg_rtt_ms is not None:
                latencies.append(hop.avg_rtt_ms)
            if hop.subnet_boundary_from_prev:
                transition_count += 1
            if hop.is_private:
                private_hops += 1
        if destination_ip and any(h.ip == destination_ip for h in run):
            reachable_runs += 1

    return {
        "target": target,
        "destination_ip_from_trace_header": destination_ip,
        "run_count": len(all_runs),
        "avg_hops_per_run": statistics.mean([len(run) for run in all_runs]) if all_runs else 0,
        "reachable_runs_detected": reachable_runs,
        "total_detected_prefix_transitions": transition_count,
        "total_private_hops": private_hops,
        "overall_avg_rtt_ms": statistics.mean(latencies) if latencies else None,
        "overall_min_rtt_ms": min(latencies) if latencies else None,
        "overall_max_rtt_ms": max(latencies) if latencies else None,
        "stability": analyze_stability(all_runs),
    }
