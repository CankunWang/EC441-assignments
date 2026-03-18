from __future__ import annotations

import ipaddress
import platform
import re
import statistics
import subprocess
from dataclasses import dataclass


WINDOWS_HOP_RE = re.compile(r"^\s*(\d+)\s+(.*)$")
RTT_RE = re.compile(r"(<\d+|\d+)\s*ms", re.IGNORECASE)
IP_RE = re.compile(r"\b((?:\d{1,3}\.){3}\d{1,3})\b")
HEADER_IP_RE = re.compile(r"\[([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)\]")


@dataclass
class HopResult:
    hop: int
    ip: str | None
    rtts_ms: list[float]
    avg_rtt_ms: float | None
    min_rtt_ms: float | None
    max_rtt_ms: float | None
    is_private: bool | None
    cidr_24: str | None
    cidr_16: str | None
    subnet_boundary_from_prev: bool
    boundary_reason: str | None
    latency_jump_from_prev_ms: float | None


def slugify_target(target: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", target.strip()).strip("_") or "target"


def default_output_root() -> str:
    if platform.system().lower() == "windows":
        return r"D:\EC441-assignments\Week 5\Lab-NetworkLayer-Traceroute"
    return "network_lab_outputs"


def build_trace_command(target: str, max_hops: int, timeout_ms: int) -> list[str]:
    if platform.system().lower() == "windows":
        return ["tracert", "-d", "-h", str(max_hops), "-w", str(timeout_ms), target]
    wait_sec = max(1, int(round(timeout_ms / 1000)))
    return ["traceroute", "-n", "-m", str(max_hops), "-w", str(wait_sec), target]


def parse_rtt(token: str) -> float:
    if token.startswith("<"):
        return 1.0
    return float(token)


def classify_ip(ip: str | None) -> tuple[bool | None, str | None, str | None]:
    if not ip:
        return None, None, None
    try:
        addr = ipaddress.ip_address(ip)
        return (
            bool(addr.is_private),
            str(ipaddress.ip_network(f"{ip}/24", strict=False)),
            str(ipaddress.ip_network(f"{ip}/16", strict=False)),
        )
    except ValueError:
        return None, None, None


def parse_traceroute_output(raw_text: str) -> tuple[list[dict], str | None]:
    hops = []
    destination_ip = None

    for line in raw_text.splitlines():
        if destination_ip is None:
            match_dest = HEADER_IP_RE.search(line)
            if match_dest:
                destination_ip = match_dest.group(1)

        match = WINDOWS_HOP_RE.match(line)
        if not match:
            continue

        hop_num = int(match.group(1))
        body = match.group(2)
        rtts = [parse_rtt(x.lower()) for x in RTT_RE.findall(body)]

        ip = None
        ip_candidates = IP_RE.findall(body)
        if ip_candidates:
            ip = ip_candidates[-1]

        is_private, cidr_24, cidr_16 = classify_ip(ip)
        avg_rtt = statistics.mean(rtts) if rtts else None

        hops.append(
            {
                "hop": hop_num,
                "ip": ip,
                "rtts_ms": rtts,
                "avg_rtt_ms": avg_rtt,
                "min_rtt_ms": min(rtts) if rtts else None,
                "max_rtt_ms": max(rtts) if rtts else None,
                "is_private": is_private,
                "cidr_24": cidr_24,
                "cidr_16": cidr_16,
            }
        )

    return hops, destination_ip


def infer_boundaries_and_latency(hops: list[dict]) -> list[HopResult]:
    results = []
    prev_ip = None
    prev_avg = None
    prev_24 = None
    prev_16 = None

    for hop in hops:
        ip = hop["ip"]
        avg = hop["avg_rtt_ms"]
        net24 = hop["cidr_24"]
        net16 = hop["cidr_16"]

        boundary = False
        reason = None
        if ip and prev_ip:
            if net16 and prev_16 and net16 != prev_16:
                boundary = True
                reason = "major_prefix_change_/16"
            elif net24 and prev_24 and net24 != prev_24:
                boundary = True
                reason = "subnet_change_/24"

        latency_jump = None
        if avg is not None and prev_avg is not None:
            latency_jump = avg - prev_avg
            if latency_jump >= 20 and reason is None:
                reason = "latency_increase_without_prefix_change"

        results.append(
            HopResult(
                hop=hop["hop"],
                ip=ip,
                rtts_ms=hop["rtts_ms"],
                avg_rtt_ms=avg,
                min_rtt_ms=hop["min_rtt_ms"],
                max_rtt_ms=hop["max_rtt_ms"],
                is_private=hop["is_private"],
                cidr_24=net24,
                cidr_16=net16,
                subnet_boundary_from_prev=boundary,
                boundary_reason=reason,
                latency_jump_from_prev_ms=latency_jump,
            )
        )

        if ip:
            prev_ip = ip
            prev_24 = net24
            prev_16 = net16
        if avg is not None:
            prev_avg = avg

    return results


def run_trace_once(target: str, max_hops: int, timeout_ms: int) -> dict:
    command = build_trace_command(target, max_hops=max_hops, timeout_ms=timeout_ms)
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    raw = completed.stdout if completed.stdout else completed.stderr
    parsed_hops, destination_ip = parse_traceroute_output(raw)
    hops = infer_boundaries_and_latency(parsed_hops)

    return {
        "raw": raw,
        "hops": hops,
        "destination_ip": destination_ip,
        "command": command,
        "return_code": completed.returncode,
    }
