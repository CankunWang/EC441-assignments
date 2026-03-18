#!/usr/bin/env python3
"""
EC441 Week 5 Lab:
Run repeated traceroute, parse hop data, and analyze CIDR/subnet transitions.
"""

from __future__ import annotations

import argparse
import os
import platform
import time
from datetime import datetime
from pathlib import Path

from analysis_tools import summarize_runs
from io_tools import export_hops_csv, save_summary_json, write_markdown_report
from trace_tools import default_output_root, run_trace_once, slugify_target


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="EC441 traceroute + CIDR + subnet analysis")
    parser.add_argument("--target", help="Single target, e.g. google.com")
    parser.add_argument("--targets", nargs="+", help="Multiple targets, e.g. --targets google.com 1.1.1.1")
    parser.add_argument("--runs", type=int, default=3, help="Traceroute runs per target")
    parser.add_argument("--max-hops", type=int, default=30, help="Max hops for traceroute")
    parser.add_argument("--timeout-ms", type=int, default=900, help="Probe timeout in ms")
    parser.add_argument("--pause-sec", type=float, default=0.5, help="Pause between runs")
    parser.add_argument("--export-markdown", action="store_true", help="Also save report.md")
    parser.add_argument("--output-root", default=default_output_root(), help="Root output folder")
    return parser.parse_args()


def build_metadata(args: argparse.Namespace, run_metadata: list[dict]) -> dict:
    return {
        "host": os.environ.get("COMPUTERNAME") or os.environ.get("HOSTNAME"),
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "parameters": {
            "runs": args.runs,
            "max_hops": args.max_hops,
            "timeout_ms": args.timeout_ms,
            "pause_sec": args.pause_sec,
        },
        "run_metadata": run_metadata,
    }


def run_for_target(target: str, args: argparse.Namespace, session_dir: Path) -> str:
    target_dir = session_dir / slugify_target(target) / datetime.now().strftime("%Y%m%d_%H%M%S")
    target_dir.mkdir(parents=True, exist_ok=True)

    all_runs = []
    run_metadata = []
    errors = []
    first_destination_ip = None

    for i in range(1, args.runs + 1):
        started_at = datetime.now().isoformat(timespec="seconds")
        try:
            result = run_trace_once(target, max_hops=args.max_hops, timeout_ms=args.timeout_ms)
            hops = result["hops"]
            destination_ip = result["destination_ip"]
            if first_destination_ip is None and destination_ip is not None:
                first_destination_ip = destination_ip

            (target_dir / f"raw_traceroute_run{i}.txt").write_text(result["raw"], encoding="utf-8")
            export_hops_csv(hops, target_dir / f"hops_run{i}.csv")
            all_runs.append(hops)

            run_metadata.append(
                {
                    "run_index": i,
                    "started_at": started_at,
                    "command": result["command"],
                    "return_code": result["return_code"],
                    "hop_count": len(hops),
                    "resolved_destination_ip": destination_ip,
                }
            )
        except Exception as exc:
            errors.append(f"run_{i}: {exc}")

        if i != args.runs and args.pause_sec > 0:
            time.sleep(args.pause_sec)

    summary = summarize_runs(target, first_destination_ip, all_runs)
    summary["errors"] = errors
    summary["metadata"] = build_metadata(args, run_metadata)

    save_summary_json(summary, target_dir / "analysis_summary.json")
    if args.export_markdown:
        write_markdown_report(target_dir / "report.md", summary, all_runs)

    return str(target_dir)


def main() -> None:
    args = parse_args()
    targets = args.targets if args.targets else ([args.target] if args.target else [])
    if not targets:
        raise SystemExit("Please set --target or --targets.")

    session_name = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    session_dir = Path(args.output_root).expanduser().resolve() / session_name
    session_dir.mkdir(parents=True, exist_ok=True)

    output_dirs = [run_for_target(target, args, session_dir) for target in targets]
    print("\n".join(output_dirs))


if __name__ == "__main__":
    main()
