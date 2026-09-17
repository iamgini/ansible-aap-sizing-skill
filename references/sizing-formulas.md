# Sizing Formulas

All formulas sourced from Red Hat official documentation. `A:` marks planning defaults not yet
validated by primary-source measurement. Quote the formula and its inputs next to every number in
the output files.

---

## Execution Node Memory (the core formula)

**Source:** Red Hat AAP Planning Guide 2.6 — "System requirements"

```
required_ram_gb = ceil(forks / 10) + 2
```

Where:
- `forks` = the forks value set in job templates or `ansible.cfg` (ask if unknown; `A: 5` default)
- `2` = base reservation for automation controller overhead
- Result is per execution/hybrid node

**Examples:**

| Forks | Required RAM |
|---:|---:|
| 5 (default) | 3 GB (min 16 GB node) |
| 50 | 7 GB |
| 100 | 12 GB |
| 200 | 22 GB |
| 400 | 42 GB |

> Always round up to next standard node size (16 / 32 / 64 / 128 GB).

---

## Execution Node Count

**Source:** derived from capacity formula in AAP Planning Guide; burst reserve from AAP
Optimization Guide 2.6.

```
execution_capacity_per_node = (ram_gb - 2) * 10    # inverse of memory formula above
jobs_per_node = floor(execution_capacity_per_node / forks)
raw_nodes = ceil(peak_concurrent_jobs / jobs_per_node)
nodes_with_burst = ceil(raw_nodes * BURST_RESERVE)     # A: BURST_RESERVE = 1.30
nodes_ha = max(nodes_with_burst, HA_MINIMUM)           # A: HA_MINIMUM = 2
```

**Constants:**
- `BURST_RESERVE = 1.30` — A: 30% burst headroom; replace with measured p95/p99 peak
- `HA_MINIMUM = 2` — minimum replicas for production HA

---

## Execution Capacity Units (AWX internal)

**Source:** AAP Planning Guide — "Capacity planning"

```
capacity_units_needed = (concurrent_jobs × forks) + (concurrent_jobs × 1)
```

The `× 1` accounts for the base control task per job. Each node contributes its
`(ram_gb - 2) × 10` capacity units.

---

## Database Storage Growth

**Source:** A: derived from AAP Planning Guide storage guidance; UNVERIFIED exact coefficients.

```
db_growth_gb_per_week ≈ (managed_hosts × jobs_per_day × tasks_per_job × avg_events_per_task
                          × bytes_per_event) / 1e9
```

**Planning defaults (A: UNVERIFIED):**
- `avg_events_per_task ≈ 3`
- `bytes_per_event ≈ 500 B`
- `retention_days`: default 180 days (configurable in controller settings)

**Example:** 250 hosts × 24 jobs/day × 20 tasks × 3 events × 500 B = ~180 MB/day = ~1.2 GB/week

Allocate at least 6 months of projected growth; add 20% headroom.

---

## Private Automation Hub Storage

**Source:** A: UNVERIFIED planning default; no primary-source formula in Red Hat docs (measure).

```
hub_storage_gb ≈ (collections_count × avg_collection_size_mb × mirror_depth) / 1000
                  + container_registry_gb
                  + sync_overhead_factor
```

**Planning defaults (A: UNVERIFIED):**
- `avg_collection_size_mb ≈ 50 MB` per collection version
- `mirror_depth`: number of versions retained per collection (A: 3)
- `container_registry_gb`: EE images (A: 20 GB per EE image × number of EEs)
- `sync_overhead_factor`: A: 1.30 (30% overhead for metadata, indexes, temp space)

Ask: how many collections synced from Galaxy/Automation Hub? Which EEs stored?

---

## EDA (Event-Driven Ansible) Sizing

**Source:** A: UNVERIFIED planning defaults; EDA sizing not formally documented in AAP 2.6 docs.

```
decision_environments_needed = ceil(rulebook_activations / activations_per_de)
```

**Planning defaults (A: UNVERIFIED):**
- `activations_per_de ≈ 10` concurrent rulebook activations per decision environment
- Each DE: A: 2 vCPU / 4 GB RAM per active rulebook activation set
- Events/s throughput: A: 100–500 events/s per DE (highly workload-dependent — measure)

Ask: how many rulebooks run concurrently? What is the expected events/s peak?

---

## Growth Path

Scale in 2× increments (from AAP Optimization Guide 2.6):

| Current | Next scale step |
|---|---|
| 16 GB RAM | 32 GB |
| 32 GB RAM | 64 GB |
| 4 vCPU | 8 vCPU |
| 8 vCPU | 16 vCPU |

Add execution nodes horizontally before scaling control nodes vertically.
For OCP: adjust pod resource limits and add worker nodes before adjusting requests.

---

## Sensitivity Ranges

All throughput and capacity figures are planning estimates with inherent uncertainty. Always include
a sensitivity range in the output and flag for load-test validation before procurement.

| Formula input | Conservative | Midpoint (default) | Optimistic |
|---|---|---|---|
| Burst reserve | 1.50 | 1.30 | 1.10 |
| HA minimum replicas | 3 | 2 | 1 (not recommended) |
| DB bytes/event | 800 B | 500 B | 300 B |
| EDA activations/DE | 5 | 10 | 20 |
