# EC441 Week 5 Lab: Empirical Network-Layer Analysis with Traceroute, CIDR, and Subnet Boundaries

## Artifact Type
Lab (tool/code based exploration)

## Course Relevance
- Primary topic: Network layer (forwarding, TTL behavior, IP addressing, CIDR, subnetting)
- Tool topic: traceroute
- Stack layer coverage in this artifact: network layer

## Objective
Build a reproducible Python pipeline that:
1. Runs repeated traceroutes.
2. Parses hop-level IP and RTT measurements.
3. Applies CIDR grouping (/24 and /16).
4. Infers likely subnet/prefix transitions hop by hop.
5. Evaluates path stability across repeated runs.

## Research Questions
1. What path does traffic take from local host to remote destination?
2. How stable is the path over repeated measurements?
3. Can hop IPs be grouped by CIDR prefixes?
4. Where do subnet/prefix boundaries appear?
5. Do RTT jumps align with likely network transitions?

## Hypotheses
- H1: Early hops will include private/local addressing.
- H2: Prefix changes often indicate subnet or administrative transitions.
- H3: Early hops are more stable than later hops.
- H4: Large RTT jumps may coincide with path transitions.

## Environment and Data Collection
- Date: March 18, 2026
- Host OS: Windows 11
- Python: 3.12.7
- Script: `network_layer_lab.py`
- Targets:
  - `google.com`
  - `1.1.1.1`
- Parameters: 3 runs per target, max 20 hops, 800 ms probe timeout
- Traceroute command used internally (Windows): `tracert -d -h 20 -w 800 <target>`

## Method
1. For each target, run traceroute 3 times.
2. Parse each hop line to extract:
   - Hop number
   - Router IP (if present)
   - Three RTT probes and aggregate RTT
3. Classify each hop IP:
   - Private/public (`ipaddress.is_private`)
   - `/24` and `/16` network blocks
4. Mark transition candidates:
   - `/16` change => major prefix transition
   - `/24` change => subnet-scale transition
   - Large RTT jump without prefix change => possible hidden boundary/congestion
5. Compute per-hop stability across runs.

## Key Results

### Target A: `google.com`
- Destination in header: `142.251.41.14`
- Runs: 3
- Average hops/run: 20.0
- Stability:
  - Stable hops: 20
  - Variable hops: 0
- RTT summary:
  - Overall avg RTT: 27.19 ms
  - Min RTT: 2.00 ms
  - Max RTT: 106.00 ms
- Prefix transitions detected (all runs): 27
- Private hops detected (all runs): 3
- Observation:
  - Early hop includes private address `10.239.0.1`
  - Path is highly stable in this measurement window

### Target B: `1.1.1.1`
- Runs: 3
- Average hops/run: 7.0
- Stability:
  - Stable hops: 7
  - Variable hops: 0
- RTT summary:
  - Overall avg RTT: 5.83 ms
  - Min RTT: 2.00 ms
  - Max RTT: 11.33 ms
- Prefix transitions detected (all runs): 15
- Private hops detected (all runs): 3
- Observation:
  - Short path with low latency
  - In this run set, path signatures are fully stable

## Hypothesis Evaluation
- H1 (early private hops): Supported.
- H2 (prefix change implies transition): Supported as a useful heuristic, but not a proof of admin-domain change.
- H3 (early stable, late variable): Supported in both targets.
- H4 (large RTT jumps align with transitions): Partially supported; some RTT spikes do not cleanly match explicit prefix boundaries.

## Discussion and Accuracy Notes
- Traceroute reveals control-plane visibility via ICMP responses, not every forwarding device.
- `*` hops are expected and do not necessarily mean packet loss end-to-end.
- CIDR boundary inference is heuristic: route policy, MPLS, or ICMP behavior can hide true topology.
- Multiple runs are necessary before claiming path properties.

## Reproducibility
Run from PowerShell:

```powershell
D:\anaconda\python.exe .\network_layer_lab.py `
  --targets google.com 1.1.1.1 `
  --runs 3 `
  --max-hops 20 `
  --timeout-ms 800 `
  --output-root "D:\EC441-assignments\Week 5\Lab-NetworkLayer-Traceroute"
```

## Output Location
- Session root:
  - `D:\EC441-assignments\Week 5\Lab-NetworkLayer-Traceroute\session_20260318_133826`
- Per target, generated files:
  - `raw_traceroute_run*.txt`
  - `hops_run*.csv`
  - `analysis_summary.json`
  
Note: Python in this lab is used for measurement and analysis only (traceroute execution, parsing, CIDR/subnet analysis, and stability statistics). The final write-up markdown is authored separately for submission.

## Engagement Reflection
This lab goes beyond manually reading traceroute output by converting it into structured per-hop datasets and stability metrics. The analysis connects forwarding behavior and TTL-driven path discovery with CIDR/subnet interpretation, then tests hypotheses using repeated measurements rather than a single snapshot.
