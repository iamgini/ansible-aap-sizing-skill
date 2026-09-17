#!/usr/bin/env python3
"""Deterministic AAP sizing calculator.

SECURITY / TRANSPARENCY NOTE
=============================
This script is safe to run and inspect:
  - Python 3.9+ standard library ONLY — no pip installs, no external packages.
  - NO network calls of any kind (no urllib, no socket, no subprocess to curl/wget).
  - NO file writes except to the engagement folder you specify (and only when you
    redirect output: `size.py ... > file.json`).
  - NO system calls, NO shell execution, NO environment variable leakage.
  - All logic is deterministic arithmetic — same inputs always produce same output.
  - Full source is at scripts/size.py in this repo. Read it before approving.

The .claude/settings.json in this repo pre-approves ONLY `python3 scripts/size.py*`
— nothing broader. If your agent asks to run anything else, deny it and report it.

Follows references/sizing-formulas.md. All defaults labelled A: are planning
assumptions — replace with measured values before procurement.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from typing import Any, Dict, List, Optional

# ── Constants (references/sizing-formulas.md) ──────────────────────────────
RAM_PER_10_FORKS_GB = 1.0          # 1 GB per 10 forks + 2 GB base reservation
BASE_RESERVATION_GB = 2.0          # Controller overhead per node
BURST_RESERVE = 1.30               # A: 30% burst headroom
HA_MINIMUM_NODES = 2               # Minimum execution nodes for production HA
DEFAULT_FORKS = 5                  # A: UNVERIFIED — ask the customer
DEFAULT_HA_REPLICAS = 2

# ── Topology catalog (topology-catalog.md) ─────────────────────────────────
TOPOLOGIES: Dict[str, Dict[str, Any]] = {
    "growth-a": {
        "deployment_type": "containerized",
        "description": "All-in-one (1 VM) — dev/test/demo only",
        "vm_count": 1,
        "use_case": "Development, proof-of-concept, lab",
        "max_managed_hosts": 50,
        "max_concurrent_jobs": 10,
        "ha": False,
        "nodes": [
            {"role": "all-in-one", "count": 1, "min_vcpu": 4, "min_ram_gb": 16,
             "min_disk_gb": 60, "components": "Controller+Hub+EDA+Gateway+DB"},
        ],
        "reference": "ansible/test-topologies cont-a.env-a",
    },
    "growth-b": {
        "deployment_type": "containerized",
        "description": "Separated DB (2–3 VMs) — small production",
        "vm_count": 3,
        "use_case": "Small production, up to ~200 managed hosts",
        "max_managed_hosts": 200,
        "max_concurrent_jobs": 25,
        "ha": False,
        "nodes": [
            {"role": "controller+hub+eda+gateway", "count": 1, "min_vcpu": 8, "min_ram_gb": 32,
             "min_disk_gb": 80, "components": "Controller+Hub+EDA+Gateway"},
            {"role": "db", "count": 1, "min_vcpu": 4, "min_ram_gb": 16,
             "min_disk_gb": 100, "components": "PostgreSQL"},
            {"role": "execution", "count": 1, "min_vcpu": 8, "min_ram_gb": 16,
             "min_disk_gb": 40, "components": "Execution node"},
        ],
        "reference": "ansible/test-topologies cont-b.env-a",
    },
    "enterprise-a": {
        "deployment_type": "containerized",
        "description": "Separated components (5–7 VMs) — medium production",
        "vm_count": 6,
        "use_case": "Medium production, 200–1000 managed hosts",
        "max_managed_hosts": 1000,
        "max_concurrent_jobs": 100,
        "ha": True,
        "nodes": [
            {"role": "controller", "count": 2, "min_vcpu": 8, "min_ram_gb": 32,
             "min_disk_gb": 80, "components": "Controller+Gateway"},
            {"role": "hub", "count": 1, "min_vcpu": 8, "min_ram_gb": 32,
             "min_disk_gb": 500, "components": "Private Automation Hub"},
            {"role": "eda", "count": 1, "min_vcpu": 4, "min_ram_gb": 16,
             "min_disk_gb": 40, "components": "EDA"},
            {"role": "db", "count": 1, "min_vcpu": 4, "min_ram_gb": 16,
             "min_disk_gb": 200, "components": "PostgreSQL"},
            {"role": "execution", "count": 2, "min_vcpu": 8, "min_ram_gb": 32,
             "min_disk_gb": 40, "components": "Execution nodes"},
        ],
        "reference": "ansible/test-topologies — enterprise pattern",
    },
    "enterprise-b": {
        "deployment_type": "containerized",
        "description": "Fully resilient (10+ VMs) — large production HA",
        "vm_count": 11,
        "use_case": "Large production, 1000+ managed hosts, HA required",
        "max_managed_hosts": 5000,
        "max_concurrent_jobs": 500,
        "ha": True,
        "nodes": [
            {"role": "controller", "count": 3, "min_vcpu": 16, "min_ram_gb": 64,
             "min_disk_gb": 100, "components": "Controller+Gateway (active/active)"},
            {"role": "hub", "count": 2, "min_vcpu": 8, "min_ram_gb": 32,
             "min_disk_gb": 1000, "components": "Private Automation Hub (HA pair)"},
            {"role": "eda", "count": 2, "min_vcpu": 8, "min_ram_gb": 32,
             "min_disk_gb": 40, "components": "EDA (HA pair)"},
            {"role": "db", "count": 2, "min_vcpu": 8, "min_ram_gb": 32,
             "min_disk_gb": 500, "components": "PostgreSQL (primary + replica)"},
            {"role": "execution", "count": 4, "min_vcpu": 16, "min_ram_gb": 64,
             "min_disk_gb": 40, "components": "Execution nodes"},
        ],
        "reference": "ansible/test-topologies — resilient pattern",
    },
    "ocp-growth": {
        "deployment_type": "ocp",
        "description": "OCP single namespace — small/dev deployments",
        "vm_count": 3,
        "use_case": "OCP-hosted AAP, small scale or dev",
        "max_managed_hosts": 200,
        "max_concurrent_jobs": 20,
        "ha": False,
        "nodes": [
            {"role": "ocp-worker", "count": 3, "min_vcpu": 4, "min_ram_gb": 16,
             "min_disk_gb": 100, "components": "AAP pods (Controller+Hub+EDA+Gateway)"},
        ],
        "reference": "ansible/test-topologies ocp-a.env-a",
    },
    "ocp-enterprise": {
        "deployment_type": "ocp",
        "description": "OCP multi-namespace HA — enterprise scale",
        "vm_count": 6,
        "use_case": "OCP-hosted AAP, enterprise, HA worker pool",
        "max_managed_hosts": 2000,
        "max_concurrent_jobs": 200,
        "ha": True,
        "nodes": [
            {"role": "ocp-worker", "count": 6, "min_vcpu": 8, "min_ram_gb": 32,
             "min_disk_gb": 200, "components": "AAP pods (distributed across workers)"},
        ],
        "reference": "ansible/test-topologies ocp-b.env-a",
    },
}

# OCP pod resource baselines (references/component-sizing.md)
OCP_POD_SPECS = {
    "task": {
        "description": "Automation Controller — task pod (ansible-runner, job dispatch)",
        "requests": {"cpu": "1000m", "memory": "8Gi"},
        "limits":   {"cpu": "4000m", "memory": "8Gi"},
    },
    "web": {
        "description": "Automation Controller — web pod (REST API, UI)",
        "requests": {"cpu": "500m",  "memory": "1.5Gi"},
        "limits":   {"cpu": "2000m", "memory": "1.5Gi"},
    },
    "redis": {
        "description": "Redis (session cache, celery broker)",
        "requests": {"cpu": "250m",  "memory": "1.5Gi"},
        "limits":   {"cpu": "500m",  "memory": "1.5Gi"},
    },
    "ee": {
        "description": "Execution Environment pod (Container Group — per-job ephemeral pod)",
        "requests": {"cpu": "100m",  "memory": "400Mi"},
        "limits":   {"cpu": "500m",  "memory": "400Mi"},
    },
}


# ── Formatters ──────────────────────────────────────────────────────────────

def _table(headers: List[str], rows: List[List[str]]) -> str:
    widths = [max(len(h), max((len(str(r[i])) for r in rows), default=0))
              for i, h in enumerate(headers)]
    sep = "| " + " | ".join("-" * w for w in widths) + " |"
    hdr = "| " + " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers)) + " |"
    body = "\n".join(
        "| " + " | ".join(str(r[i]).ljust(widths[i]) for i in range(len(headers))) + " |"
        for r in rows
    )
    return f"{hdr}\n{sep}\n{body}"


def _out(data: Any, fmt: str) -> None:
    if fmt == "json":
        print(json.dumps(data, indent=2))
    elif fmt == "md":
        if isinstance(data, str):
            print(data)
        else:
            print(json.dumps(data, indent=2))
    else:
        if isinstance(data, str):
            print(data)
        else:
            print(json.dumps(data, indent=2))


# ── Subcommand: execution-nodes ─────────────────────────────────────────────

def cmd_execution_nodes(args: argparse.Namespace) -> None:
    """Size execution nodes from concurrent jobs and forks.

    Formula (references/sizing-formulas.md):
      ram_needed_gb = ceil(forks / 10) + 2     (1 GB per 10 forks + 2 GB base)
      jobs_per_node = floor((ram_per_node - 2) * 10 / forks)
      raw_nodes     = ceil(concurrent_jobs / jobs_per_node)
      nodes_burst   = ceil(raw_nodes * BURST_RESERVE)
      nodes_final   = max(nodes_burst, ha_replicas)
    """
    forks = args.forks
    concurrent = args.concurrent_jobs
    ram = args.ram_per_node
    ha = args.ha_replicas

    if args.dry_run:
        print("## Dry run — formula preview (no calculation performed)")
        print("")
        print(f"  Formula : ram_needed_gb = ceil(forks / 10) + {BASE_RESERVATION_GB}")
        print(f"            jobs_per_node = floor((ram_per_node - {BASE_RESERVATION_GB}) * 10 / forks)")
        print(f"            raw_nodes     = ceil(concurrent_jobs / jobs_per_node)")
        print(f"            nodes_final   = max(ceil(raw_nodes * {BURST_RESERVE}), ha_replicas)")
        print(f"  Inputs  : concurrent_jobs={concurrent}, forks={forks}, "
              f"ram_per_node={ram} GB, ha_replicas={ha}")
        print(f"  Source  : Red Hat AAP Planning Guide 2.6 — 'System requirements'")
        print(f"  Script  : scripts/size.py (stdlib only, no network, no file writes)")
        return

    ram_needed_gb = math.ceil(forks / 10) + BASE_RESERVATION_GB
    jobs_per_node = max(1, int((ram - BASE_RESERVATION_GB) * 10 / forks))
    raw_nodes = math.ceil(concurrent / jobs_per_node)
    nodes_burst = math.ceil(raw_nodes * BURST_RESERVE)
    nodes_final = max(nodes_burst, ha)

    capacity_units_per_node = jobs_per_node * forks + jobs_per_node  # (jobs × forks) + (jobs × 1)
    total_capacity_units = nodes_final * capacity_units_per_node
    peak_demand_units = concurrent * forks + concurrent

    result: Dict[str, Any] = {
        "inputs": {
            "concurrent_jobs": concurrent,
            "forks": forks,
            "ram_per_node_gb": ram,
            "ha_replicas": ha,
            "burst_reserve": BURST_RESERVE,
        },
        "formula": {
            "ram_needed_per_node_gb": ram_needed_gb,
            "jobs_per_node": jobs_per_node,
            "raw_nodes": raw_nodes,
            "nodes_after_burst_reserve": nodes_burst,
            "nodes_final_ha_min": nodes_final,
        },
        "recommendation": {
            "execution_nodes": nodes_final,
            "ram_per_node_gb": ram,
            "capacity_units_per_node": capacity_units_per_node,
            "total_capacity_units": total_capacity_units,
            "peak_demand_units": peak_demand_units,
            "headroom_pct": round((total_capacity_units - peak_demand_units)
                                  / total_capacity_units * 100, 1),
        },
        "binding_constraint": (
            "memory (RAM for forks)" if ram_needed_gb >= ram * 0.8
            else "concurrency (job slots)"
        ),
        "notes": [
            f"A: forks={forks} — replace with measured value from job templates / ansible.cfg",
            f"A: BURST_RESERVE={BURST_RESERVE} — replace with measured p95 peak concurrent jobs",
            "Not included: rolling-update capacity (+1 node), one-node-down (--ha-mode node)",
            "Validate with load test before procurement (target: queue depth near zero at peak)",
        ],
    }

    if args.format == "json":
        print(json.dumps(result, indent=2))
        return

    lines = [
        f"## Execution Node Sizing",
        f"",
        _table(
            ["Input", "Value", "Provenance"],
            [
                ["Concurrent jobs", str(concurrent), "Engagement brief / A:"],
                ["Forks per job", str(forks), "A: planning default — measure"],
                ["RAM per node", f"{ram} GB", "Engagement brief / A:"],
                ["HA replicas min", str(ha), f"A: production minimum"],
            ]
        ),
        f"",
        f"### Formula trace",
        f"",
        f"```",
        f"ram_needed_gb    = ceil({forks} / 10) + 2 = {ram_needed_gb} GB",
        f"jobs_per_node    = floor(({ram} - 2) × 10 / {forks}) = {jobs_per_node}",
        f"raw_nodes        = ceil({concurrent} / {jobs_per_node}) = {raw_nodes}",
        f"nodes_burst      = ceil({raw_nodes} × {BURST_RESERVE}) = {nodes_burst}",
        f"nodes_final      = max({nodes_burst}, HA min {ha}) = {nodes_final}",
        f"```",
        f"",
        _table(
            ["Metric", "Value"],
            [
                ["Execution nodes recommended", str(nodes_final)],
                ["RAM per node", f"{ram} GB"],
                ["Capacity units per node", str(capacity_units_per_node)],
                ["Total capacity units", str(total_capacity_units)],
                ["Peak demand units", str(peak_demand_units)],
                ["Headroom", f"{result['recommendation']['headroom_pct']}%"],
                ["Binding constraint", result["binding_constraint"]],
            ]
        ),
        f"",
        f"> A: All throughput figures are planning estimates. Run a load test at {concurrent} "
        f"concurrent jobs before procurement.",
    ]

    if args.explain:
        lines += [
            f"",
            f"### Sensitivity (replace burst_reserve with measured p95 peak)",
            f"",
            _table(
                ["Burst reserve", "Nodes after burst", "Nodes final"],
                [
                    ["1.10 (optimistic)", str(math.ceil(raw_nodes * 1.10)),
                     str(max(math.ceil(raw_nodes * 1.10), ha))],
                    [f"{BURST_RESERVE} (default)", str(nodes_burst), str(nodes_final)],
                    ["1.50 (conservative)", str(math.ceil(raw_nodes * 1.50)),
                     str(max(math.ceil(raw_nodes * 1.50), ha))],
                ]
            ),
        ]

    print("\n".join(lines))


# ── Subcommand: topology ─────────────────────────────────────────────────────

def cmd_topology(args: argparse.Namespace) -> None:
    """Show topology VM/node BOM for a named topology."""
    topo_key = args.topology
    if topo_key not in TOPOLOGIES:
        print(f"ERROR: unknown topology '{topo_key}'. Available: {', '.join(TOPOLOGIES)}", file=sys.stderr)
        sys.exit(1)

    topo = TOPOLOGIES[topo_key]

    if args.deployment_type and args.deployment_type != topo["deployment_type"]:
        print(f"WARNING: topology '{topo_key}' is for '{topo['deployment_type']}', "
              f"not '{args.deployment_type}'", file=sys.stderr)

    if args.managed_hosts and args.managed_hosts > topo["max_managed_hosts"]:
        print(f"WARNING: {args.managed_hosts} managed hosts exceeds topology planning limit "
              f"({topo['max_managed_hosts']}). Consider a larger topology.", file=sys.stderr)

    if args.concurrent_jobs and args.concurrent_jobs > topo["max_concurrent_jobs"]:
        print(f"WARNING: {args.concurrent_jobs} concurrent jobs exceeds topology planning limit "
              f"({topo['max_concurrent_jobs']}). Add execution nodes or choose a larger topology.", file=sys.stderr)

    if args.format == "json":
        print(json.dumps({"topology": topo_key, **topo}, indent=2))
        return

    lines = [
        f"## Topology: `{topo_key}`",
        f"",
        f"**{topo['description']}**",
        f"Use case: {topo['use_case']}",
        f"HA: {'Yes' if topo['ha'] else 'No'}",
        f"Reference: {topo['reference']}",
        f"",
        _table(
            ["Role", "Count", "Min vCPU", "Min RAM", "Min Disk", "Components"],
            [
                [n["role"], str(n["count"]), str(n["min_vcpu"]),
                 f"{n['min_ram_gb']} GB", f"{n['min_disk_gb']} GB", n["components"]]
                for n in topo["nodes"]
            ]
        ),
        f"",
        f"Total VMs/nodes: {topo['vm_count']}",
        f"Planning limits: ≤{topo['max_managed_hosts']} managed hosts, "
        f"≤{topo['max_concurrent_jobs']} concurrent jobs (A: planning defaults)",
        f"",
        f"> Cross-check with ansible/test-topologies for validated inventory: "
        f"https://github.com/ansible/test-topologies",
    ]
    print("\n".join(lines))


# ── Subcommand: component ────────────────────────────────────────────────────

def cmd_component(args: argparse.Namespace) -> None:
    """Per-component resource sizing. See references/component-sizing.md for full specs."""
    component = args.component
    print(f"# Component sizing: {component}")
    print(f"")
    print(f"See references/component-sizing.md for full resource tables and OCP pod YAML.")
    print(f"")

    guidance = {
        "controller": (
            f"Automation Controller sizing driver: concurrent jobs + event processing throughput.\n"
            f"  A: Minimum: 4 vCPU / 16 GB RAM (dev). Production: 8 vCPU / 32 GB RAM.\n"
            f"  Disk /var/lib/awx: 20 GB minimum; 50 GB+ for EE image cache.\n"
            f"  Run: python3 scripts/size.py ocp-pods  (for OCP pod requests/limits YAML)"
        ),
        "hub": (
            f"Private Automation Hub sizing driver: collection count × avg size × mirror depth.\n"
            f"  A: Minimum: 4 vCPU / 16 GB RAM. Production: 8 vCPU / 32 GB RAM.\n"
            f"  A: Storage = collections × 50 MB × mirror_depth + EE registry + 30% overhead.\n"
            f"  Ask: how many collections synced? How many EE images stored?"
        ),
        "eda": (
            f"EDA sizing driver: rulebook activations × resources per decision environment.\n"
            f"  A: Minimum: 2 vCPU / 8 GB RAM. Production: 4 vCPU / 16 GB RAM.\n"
            f"  A: ~10 rulebook activations per decision environment (UNVERIFIED — measure).\n"
            f"  Ask: how many rulebooks run concurrently? Peak events/s?"
        ),
        "gateway": (
            f"AAP Gateway sizing driver: API throughput + SSO session load.\n"
            f"  A: Lightweight proxy; 2 vCPU / 4 GB RAM typically sufficient.\n"
            f"  Production with HA: 2 instances behind load balancer."
        ),
        "db": (
            f"PostgreSQL sizing driver: managed hosts × jobs/day × tasks × retention.\n"
            f"  A: Minimum: 4 vCPU / 16 GB RAM. Production: 8 vCPU / 32 GB RAM.\n"
            f"  A: Storage growth ~ managed_hosts × jobs_per_day × 20 tasks × 500 B/event × 180 days.\n"
            f"  AAP 2.6+ supports PostgreSQL 15, 16, 17."
        ),
    }

    if component in guidance:
        print(guidance[component])
    else:
        print(f"Unknown component '{component}'. Available: {', '.join(guidance)}")


# ── Subcommand: ocp-pods ─────────────────────────────────────────────────────

def cmd_ocp_pods(args: argparse.Namespace) -> None:
    """Print OCP pod resource requests/limits baseline YAML."""
    if args.format == "json":
        print(json.dumps(OCP_POD_SPECS, indent=2))
        return

    if args.format in ("yaml", "md"):
        print("# AAP OCP Pod Resource Baseline")
        print("# Source: Red Hat AAP 2.6 Optimization Guide (performance benchmarks)")
        print("# A: Adjust limits based on your workload profile and load test results.")
        print("")
        for key, spec in OCP_POD_SPECS.items():
            print(f"# {spec['description']}")
            print(f"{key}_resource_requirements:")
            print(f"  requests:")
            print(f"    cpu: \"{spec['requests']['cpu']}\"")
            print(f"    memory: \"{spec['requests']['memory']}\"")
            print(f"  limits:")
            print(f"    cpu: \"{spec['limits']['cpu']}\"")
            print(f"    memory: \"{spec['limits']['memory']}\"")
            print("")
    else:
        for key, spec in OCP_POD_SPECS.items():
            print(f"{key}: requests {spec['requests']} / limits {spec['limits']} — {spec['description']}")


# ── Subcommand: mesh ─────────────────────────────────────────────────────────

def cmd_mesh(args: argparse.Namespace) -> None:
    """Automation Mesh node design. See references/node-sizing.md."""
    print("# Automation Mesh Design")
    print("")
    print(f"Execution nodes: {args.execution_nodes}")
    if args.sites > 1:
        print(f"Sites: {args.sites} — hop nodes recommended for inter-site routing")
        hop_nodes = args.hop_nodes or args.sites
        print(f"Hop nodes: {hop_nodes} (A: 1 per remote site minimum)")
    else:
        print(f"Sites: 1 — no hop nodes required (single-site deployment)")
    print("")
    print("Node type summary:")
    print("  Control/Hybrid : managed by the topology (see 'topology' subcommand)")
    print(f"  Execution      : {args.execution_nodes} (from 'execution-nodes' subcommand)")
    if args.sites > 1:
        print(f"  Hop            : {args.hop_nodes or args.sites} (relay for remote sites)")
    print("")
    print("See references/node-sizing.md for peering rules and network requirements.")
    print("See references/redhat-aap-stack.md — OCP Operator restriction: only execution")
    print("and hop nodes can be added; control/hybrid nodes not supported on OCP Operator.")


# ── Subcommand: cost ─────────────────────────────────────────────────────────

def cmd_cost(args: argparse.Namespace) -> None:
    """Indicative infrastructure cost. See references/cost-model.md."""
    print("# Cost (Indicative — planning only)")
    print("")
    print("Infrastructure cost estimate requires node count and type from the 'topology'")
    print("and 'execution-nodes' subcommands. Run those first, then use cost-model.md")
    print("to build the cost table for your chosen provider.")
    print("")
    print("AAP subscription pricing: contact your Red Hat account team or see")
    print("  https://www.redhat.com/en/technologies/management/ansible/pricing")
    print("")
    print("Never include an invented subscription price in the output.")
    print("See references/cost-model.md for cloud and on-prem infrastructure rate tables.")
    print("")
    print(f"Deployment type : {args.deployment_type}")
    print(f"Node count      : {args.nodes}")
    print(f"Provider        : {args.provider}")
    print("")
    print("A: All prices are planning defaults — use actual quotes before budgeting.")


# ── Subcommand: topologies ───────────────────────────────────────────────────

def cmd_topologies(args: argparse.Namespace) -> None:
    """List all available topology keys."""
    lines = ["## Available Topologies", ""]
    rows = [
        [key, t["deployment_type"], str(t["vm_count"]),
         f"≤{t['max_managed_hosts']}", f"≤{t['max_concurrent_jobs']}",
         "Yes" if t["ha"] else "No", t["description"]]
        for key, t in TOPOLOGIES.items()
    ]
    lines.append(_table(
        ["Key", "Type", "VMs", "Max Hosts", "Max Jobs", "HA", "Description"],
        rows
    ))
    print("\n".join(lines))


# ── CLI ──────────────────────────────────────────────────────────────────────

def main() -> None:
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument("--format", choices=["text", "md", "json", "yaml"], default="md",
                        help="Output format (default: md)")
    shared.add_argument("--dry-run", action="store_true",
                        help="Show what would be calculated (inputs + formula) without running")

    parser = argparse.ArgumentParser(
        description="AAP sizing calculator — references/sizing-formulas.md",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[shared],
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # execution-nodes
    p_en = sub.add_parser("execution-nodes", parents=[shared],
                           help="Size execution nodes from concurrent jobs and forks")
    p_en.add_argument("--concurrent-jobs", type=int, required=True,
                      help="Peak concurrent jobs (measured p95 or planning estimate)")
    p_en.add_argument("--forks", type=int, default=DEFAULT_FORKS,
                      help=f"Forks per job (A: default {DEFAULT_FORKS} — check job templates)")
    p_en.add_argument("--ram-per-node", type=int, default=32,
                      help="RAM per execution node in GB (default: 32)")
    p_en.add_argument("--ha-replicas", type=int, default=DEFAULT_HA_REPLICAS,
                      help=f"Minimum HA replicas (default: {DEFAULT_HA_REPLICAS})")
    p_en.add_argument("--explain", action="store_true",
                      help="Show sensitivity analysis")
    p_en.set_defaults(func=cmd_execution_nodes)

    # topology
    p_t = sub.add_parser("topology", parents=[shared], help="Show VM/node BOM for a named topology")
    p_t.add_argument("--topology", required=True,
                     choices=list(TOPOLOGIES.keys()),
                     help="Topology name (see: python3 size.py topologies)")
    p_t.add_argument("--deployment-type", choices=["containerized", "ocp"],
                     help="Deployment type (for validation)")
    p_t.add_argument("--managed-hosts", type=int,
                     help="Managed host count (used for limit check)")
    p_t.add_argument("--concurrent-jobs", type=int,
                     help="Concurrent jobs (used for limit check)")
    p_t.set_defaults(func=cmd_topology)

    # component
    p_c = sub.add_parser("component", parents=[shared], help="Per-component resource sizing guidance")
    p_c.add_argument("--component", required=True,
                     choices=["controller", "hub", "eda", "gateway", "db"],
                     help="AAP component to size")
    p_c.add_argument("--concurrent-jobs", type=int, help="Peak concurrent jobs")
    p_c.add_argument("--managed-hosts", type=int, help="Managed host count")
    p_c.set_defaults(func=cmd_component)

    # ocp-pods
    p_ocp = sub.add_parser("ocp-pods", parents=[shared],
                            help="OCP pod resource requests/limits baseline YAML")
    p_ocp.set_defaults(func=cmd_ocp_pods)

    # mesh
    p_m = sub.add_parser("mesh", parents=[shared], help="Automation Mesh node design")
    p_m.add_argument("--execution-nodes", type=int, required=True,
                     help="Number of execution nodes")
    p_m.add_argument("--sites", type=int, default=1,
                     help="Number of geographic sites (default: 1)")
    p_m.add_argument("--hop-nodes", type=int,
                     help="Override hop node count (default: 1 per remote site)")
    p_m.set_defaults(func=cmd_mesh)

    # cost
    p_co = sub.add_parser("cost", parents=[shared], help="Indicative infrastructure cost guidance")
    p_co.add_argument("--nodes", type=int, required=True, help="Total node count")
    p_co.add_argument("--deployment-type", choices=["containerized", "ocp"],
                      default="containerized")
    p_co.add_argument("--provider", choices=["on-prem", "aws", "azure", "gcp"],
                      default="on-prem")
    p_co.set_defaults(func=cmd_cost)

    # topologies (list)
    p_tl = sub.add_parser("topologies", parents=[shared], help="List all available topology keys")
    p_tl.set_defaults(func=cmd_topologies)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
