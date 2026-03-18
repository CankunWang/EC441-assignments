from __future__ import annotations

import csv
import json
from pathlib import Path

from trace_tools import HopResult


def export_hops_csv(hops: list[HopResult], csv_path: Path) -> None:
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "hop",
                "ip",
                "rtts_ms",
                "avg_rtt_ms",
                "min_rtt_ms",
                "max_rtt_ms",
                "is_private",
                "cidr_24",
                "cidr_16",
                "subnet_boundary_from_prev",
                "boundary_reason",
                "latency_jump_from_prev_ms",
            ]
        )

        for hop in hops:
            writer.writerow(
                [
                    hop.hop,
                    hop.ip or "",
                    ",".join(str(v) for v in hop.rtts_ms),
                    "" if hop.avg_rtt_ms is None else f"{hop.avg_rtt_ms:.2f}",
                    "" if hop.min_rtt_ms is None else f"{hop.min_rtt_ms:.2f}",
                    "" if hop.max_rtt_ms is None else f"{hop.max_rtt_ms:.2f}",
                    "" if hop.is_private is None else str(hop.is_private),
                    hop.cidr_24 or "",
                    hop.cidr_16 or "",
                    str(hop.subnet_boundary_from_prev),
                    hop.boundary_reason or "",
                    "" if hop.latency_jump_from_prev_ms is None else f"{hop.latency_jump_from_prev_ms:.2f}",
                ]
            )


def save_summary_json(summary: dict, json_path: Path) -> None:
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")


def write_markdown_report(report_path: Path, summary: dict, runs: list[list[HopResult]]) -> None:
    lines = [
        "# EC441 Network Layer Analysis Report",
        "",
        f"- Target: `{summary['target']}`",
        f"- Destination IP (header): `{summary.get('destination_ip_from_trace_header')}`",
        f"- Runs: `{summary['run_count']}`",
        f"- Avg hops/run: `{summary['avg_hops_per_run']:.2f}`",
        f"- Reachable runs detected: `{summary['reachable_runs_detected']}`",
        f"- Prefix transitions: `{summary['total_detected_prefix_transitions']}`",
        f"- Private hops (all runs): `{summary['total_private_hops']}`",
        "",
        "## Research Questions Mapping",
        "1. Packet path: see per-run CSV and path signatures in JSON.",
        "2. Path stability: see `stability.per_hop_stability`.",
        "3. CIDR grouping: columns `cidr_24` and `cidr_16`.",
        "4. Subnet boundaries: `subnet_boundary_from_prev` and `boundary_reason`.",
        "5. Latency vs transitions: `latency_jump_from_prev_ms` compared with boundary fields.",
        "",
    ]

    for index, run in enumerate(runs, start=1):
        lines.append(f"## Run {index}")
        lines.append("hop | ip | avg_rtt_ms | cidr_24 | boundary | reason")
        lines.append("--- | --- | --- | --- | --- | ---")
        for hop in run:
            lines.append(
                f"{hop.hop} | {hop.ip or '*'} | "
                f"{'' if hop.avg_rtt_ms is None else f'{hop.avg_rtt_ms:.2f}'} | "
                f"{hop.cidr_24 or ''} | {hop.subnet_boundary_from_prev} | {hop.boundary_reason or ''}"
            )
        lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")
