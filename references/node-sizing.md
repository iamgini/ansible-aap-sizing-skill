# Node Sizing Rules

All rules are sourced from Red Hat AAP documentation unless marked `A: UNVERIFIED`. Use `A:` for
any figure applied as a planning default rather than measured from the target environment.

---

## 1. Memory — the primary sizing driver

### Core formula (sourced)

> **1 GB of RAM per 10 forks + 2 GB base reservation**
>
> Source: Red Hat AAP Planning Guide 2.6
> https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6/html/planning_your_installation/platform-system-requirements

```
node_ram_gb = ceil(forks / 10) + 2
```

**Examples:**

| Forks | RAM required |
|---:|---:|
| 10 | 3 GB |
| 50 | 7 GB |
| 100 | 12 GB |
| 200 | 22 GB |
| 400 | 42 GB |
| 512 (max) | 53 GB |

> Always round up to the next standard DIMM configuration (16/32/64/128 GB).

### Burst reserve

Apply a **1.30 burst reserve** to the derived concurrent job count before calculating forks.
Source: A: UNVERIFIED planning default; measure peak in-flight jobs from `awx_running_jobs` metric.

### Framework overhead

A: Add **2–4 GB** for OS + Ansible runner + receptor process overhead per node.

---

## 2. CPU — event processing and fork parallelism

| Node type | Min vCPU | Recommended | Sizing driver |
|---|---:|---:|---|
| Control node | 4 | 8+ | Job event processing throughput |
| Hybrid node | 4 | 8+ | Combined control + execution load |
| Execution node | 4 | 8–16 | Fork parallelism (1 CPU per 5–10 concurrent forks: A: UNVERIFIED) |
| Hop node | 2 | 4 | Receptor routing only; not compute-bound |
| Hub (API + Pulp) | 4 | 8 | Collection sync and API request throughput |
| EDA (per worker) | 2 | 4 | Rulebook evaluation throughput |
| Gateway | 2 | 4 | Proxy + SSO; lightweight |
| PostgreSQL | 4 | 8+ | DB query throughput; scale with job volume |

Source: AAP 2.6 System Requirements; A: UNVERIFIED for per-fork CPU ratios (measure under load).

---

## 3. Execution node count formula

```
execution_capacity_units = (concurrent_jobs × forks) + (concurrent_jobs × 1)
# The +1 per job is the base control task overhead (sourced: AAP Planning Guide)

node_capacity_units = (node_ram_gb - 2) × 10  # inverse of the memory formula
execution_nodes_raw = ceil(execution_capacity_units / node_capacity_units)
execution_nodes = ceil(execution_nodes_raw × BURST_RESERVE)  # 1.30
execution_nodes_ha = max(execution_nodes, HA_REPLICAS_MIN)   # 2
```

**Example:** 50 concurrent jobs, forks=10, 32 GB nodes

```
capacity_units  = (50 × 10) + (50 × 1) = 550
node_capacity   = (32 - 2) × 10 = 300 units
raw_nodes       = ceil(550 / 300) = 2
burst_nodes     = ceil(2 × 1.30) = 3
ha_minimum      = max(3, 2) = 3 execution nodes
```

---

## 4. Storage

### `/var/lib/awx` — execution environment cache

> **Minimum 20 GB** on every control and hybrid node (stores pulled execution environment container
> images).
>
> Source: AAP 2.6 Planning Guide

### Database storage growth

Database size grows with: number of managed hosts × jobs per day × tasks per job × events per task ×
retention period.

A: Planning estimate formula:

```
db_growth_gb_per_week = managed_hosts × jobs_per_day × tasks_per_job × 7 × EVENT_SIZE_KB / 1_000_000
```

Where `EVENT_SIZE_KB = 2` (A: UNVERIFIED average; measure from existing deployment).

**Example:** 500 hosts, 10 jobs/day, 20 tasks/job

```
db_growth = 500 × 10 × 20 × 7 × 2 / 1_000_000 ≈ 1.4 GB/week ≈ 73 GB/year
```

> Always set a DB maintenance/vacuum schedule and define a fact cache and job history retention
> policy (`/etc/tower/conf.d/`) to bound DB growth.

### Private Automation Hub storage

```
hub_storage_gb = collections_count × avg_collection_size_mb × mirror_depth / 1024 + sync_overhead_gb
```

Where:
- `avg_collection_size_mb` = A: 50 MB (UNVERIFIED; measure from your org's collection set)
- `mirror_depth` = number of versions retained per collection (A: 3)
- `sync_overhead_gb` = A: 20% buffer

**Example:** 200 collections, 3 versions, 50 MB avg:

```
hub_storage = 200 × 50 × 3 / 1024 + (200 × 50 × 3 / 1024 × 0.20) ≈ 29 GB + 6 GB = 35 GB
```

> Add capacity for Red Hat certified content mirror if syncing from Red Hat Automation Hub.
> A: certified content footprint 100–500 GB (UNVERIFIED; measure after first sync).

---

## 5. Network

| Link | Minimum | Recommended | Notes |
|---|---|---|---|
| Control → execution | 100 Mbps | 1 Gbps | Receptor + job artifact transfer |
| Control → DB | 1 Gbps | 1 Gbps | DB queries are latency-sensitive |
| Hub → internet / Red Hat CDN | 100 Mbps | 1 Gbps | Collection sync throughput |
| Execution → managed hosts | Per-fork SSH | 1 Gbps aggregate | SSH fan-out scales with forks |
| Hop node relay | 100 Mbps | 1 Gbps | Throughput of relayed job traffic |
| OCP worker nodes (east-west) | 10 Gbps | 25 Gbps | Pod-to-pod, DB, storage |

Source: A: UNVERIFIED planning minimums; consult AAP network requirements documentation for
specific firewall port lists.

---

## Sources

- AAP 2.6 System Requirements: https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6/install-assembly_system_requirements
- AAP 2.6 Planning Guide: https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6/html/planning_your_installation/platform-system-requirements
- AAP 2.6 Optimization Guide (PDF, May 2026): https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6/pdfs/aap-optimize-2-6-pdf.pdf
- techbeatly — Ansible Capacity Planning: https://techbeatly.com/ansible-capacity-planning/
