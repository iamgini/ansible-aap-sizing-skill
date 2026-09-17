# Output Templates

Fill every placeholder. Mark provenance as `measured`, `source-derived`, `A:` (assumption), or
`UNVERIFIED`. Section order in these templates **wins** over the summary in SKILL.md.

---

## Quick Reference Sheet

Keep to one or two pages. Lead with topology, then prove the capacity envelope.

```markdown
# <engagement> — AAP Sizing Quick Reference
_Generated: <date> | AAP version target: <version> | Deployment type: <containerized|ocp>_

> **Disclaimer — read before procurement**
>
> This document is a **planning estimate**, not a procurement specification.
> Figures marked `A:` are assumptions; figures marked `UNVERIFIED` have no primary-source backing.
> Confidence by section:
>
> | Section | Confidence | Source |
> |---|---|---|
> | Execution node RAM and count | **High** | Red Hat AAP Planning Guide (published formula) |
> | OCP pod requests/limits | **High** | Red Hat AAP Optimization Guide (benchmarked) |
> | Topology VM shapes | **High** | Red Hat AAP Planning Guide + ansible/test-topologies |
> | DB storage growth | **Medium** | Formula approach from docs; coefficients estimated |
> | Hub storage | **Medium** | No official formula — community-derived; measure after first sync |
> | EDA sizing | **Low** | Not formally documented by Red Hat; planning guess only |
> | Cost | **Indicative** | Infrastructure rates only; no subscription pricing |
>
> **Required before procurement:** load test at target concurrent job count and forks depth.
> Replace all `A:` values with measured telemetry from your environment.
> This tool plans — it does not replace a Red Hat sizing engagement or load test.

## 1. Topology

| Item | Value | Provenance |
|---|---|---|
| Topology name | <growth-a / enterprise-b / ocp-enterprise / …> | topology-catalog.md |
| Deployment type | <Containerized RHEL / OCP Operator> | Engagement brief |
| AAP version | <2.6 / 2.7> | Engagement brief |
| Total VM / node count | <N> | size.py topology |
| HA | <Yes / No / N+1 execution nodes> | Engagement brief |

## 2. Node Bill of Materials

| Role | Count | vCPU | RAM | Disk | Notes |
|---|---|---|---|---|---|
| Controller / hybrid | <N> | <N> | <GB> | <GB> | <co-located DB? EE cache?> |
| Execution | <N> | <N> | <GB> | <GB> | A: forks=<N> → <GB> RAM |
| Hub | <N> | <N> | <GB> | <GB> | <collection storage: GB> |
| EDA | <N> | <N> | <GB> | <GB> | <rulebook activations: N> |
| Gateway | <N> | <N> | <GB> | <GB> | |
| PostgreSQL | <N> | <N> | <GB> | <GB> | <managed / external> |
| Hop | <N> | <N> | <GB> | <GB> | <sites served> |

## 3. Automation Mesh Design

| Node type | Count | Sites | Peering | Notes |
|---|---|---|---|---|
| Control / hybrid | <N> | <sites> | <peers> | |
| Execution | <N> | <sites> | <peers> | |
| Hop | <N> | <sites> | <peers> | Required for: <network constraint> |

## 4. Component Resource Specs

_For OCP Operator: use Section 5 (pod YAML) instead of this table._

| Component | vCPU | RAM | Disk | Sizing driver |
|---|---|---|---|---|
| Controller (web + task + redis) | <N> | <GB> | <GB> | A: concurrent jobs=<N> |
| Hub (API + Pulp + content) | <N> | <GB> | <GB> | A: <N> collections × <MB>/collection |
| EDA | <N> | <GB> | — | A: <N> rulebook activations |
| Gateway | <N> | <GB> | — | Proxy / auth overhead |
| PostgreSQL | <N> | <GB> | <GB> | A: <N> hosts × <N> jobs/day × 180-day retention |

## 5. OCP Pod Resource Specs _(OCP Operator only — omit for containerized)_

```yaml
# Paste size.py ocp-pods output here, annotated with engagement-specific adjustments
```

## 6. Concurrency Envelope at Peak

| Metric | Value | SLO / limit | Provenance |
|---|---|---|---|
| Managed hosts | <N> | — | Engagement brief |
| Peak concurrent jobs | <N> | — | Engagement brief / A: |
| Forks per job | <N> | — | Engagement brief / A: 5 |
| Execution capacity (units) | <N> | ≥ peak demand | size.py execution-nodes |
| Peak events/s (EDA) | <N> | — | Engagement brief / A: |
| Hub sync window | <N> hr | — | Engagement brief / A: |

## 7. Assumptions

_Replace with measured values before procurement._

| # | Assumption | Default used | Measure with |
|---|---|---|---|
| A1 | Forks per job | A: 5 | `ansible.cfg` audit, job template review |
| A2 | Peak concurrent jobs | A: <N> (10% of total managed hosts / 10) | AWX API: active + pending jobs p95 |
| A3 | EDA events/s | A: <N> | Event source monitoring |
| A4 | Hub collections synced | A: <N> | Automation Hub sync config |
| … | … | … | … |

## 8. What Saturates First

`<memory (RAM for forks) | CPU (event processing) | storage (DB growth / Hub sync) | network (mesh fabric)>`

Binding constraint at peak: **<describe>**. At <N>× growth: **<describe>**.

## Validation Gate

Before procurement: run a load test at <N> concurrent jobs, forks=<N>, for <duration> and verify:
- Execution node RAM stays below 80%
- Job queue depth stays near zero at steady state
- EDA event processing lag < <threshold>
- Hub sync completes within maintenance window
```

---

## Sizing Report

```markdown
# <engagement> — AAP Sizing Report
_Generated: <date> | Prepared by: <name> | AAP version target: <version>_

> **Disclaimer — planning estimate only**
>
> | Section | Confidence | Basis |
> |---|---|---|
> | Execution node RAM and count | **High** | Published formula — Red Hat AAP Planning Guide |
> | OCP pod requests/limits | **High** | Benchmarked — Red Hat AAP Optimization Guide |
> | Topology VM shapes | **High** | Red Hat AAP Planning Guide + ansible/test-topologies |
> | DB storage growth | **Medium** | Formula from docs; coefficients estimated |
> | Hub storage | **Medium** | No official formula — community-derived; measure after first sync |
> | EDA sizing | **Low** | Not formally documented by Red Hat; planning guess only |
> | Cost | **Indicative** | Infrastructure only; dated; no subscription pricing |
>
> `A:` = assumption; `UNVERIFIED` = no primary-source backing.
> This report plans — it does not replace a Red Hat sizing engagement or pre-procurement load test.
> Replace all `A:` values with measured telemetry before ordering hardware.

## 1. Engagement Brief

| Field | Value |
|---|---|
| Customer / engagement | <name> |
| Deployment type | <Containerized RHEL / OCP Operator> |
| Scope | <greenfield / migration / scale / add-EDA / …> |
| AAP version target | <2.6 / 2.7> |
| Components in scope | <Controller, Hub, EDA, Gateway, DB> |
| Managed hosts | <N> (measured / A:) |
| Peak concurrent jobs | <N> (measured / A:) |
| Forks | <N> (measured / A:) |
| Geographic sites | <N> |
| HA requirement | <Yes/No — detail> |
| Growth horizon | <1 yr / 3 yr> |
| Existing hardware / OCP | <detail or "greenfield"> |
| Budget / subscription tier | <detail or "TBD — contact Red Hat"> |
| Disconnected install | <Yes / No> |

## 2. Topology Selection Rationale

**Selected:** `<topology-name>` — <one-line why>

**Runner-up:** `<topology-name>` — rejected because: <one-line why>

**Cross-check:** matches `ansible/test-topologies` reference topology `<cont-x.env-x / ocp-x.env-x>`.

<2–3 sentences on what drove the topology choice: scale, HA, budget, OCP vs RHEL preference.>

## 3. Calculator Trace

### Execution Node Sizing

```
python3 scripts/size.py execution-nodes \
  --concurrent-jobs <N> --forks <N> --ram-per-node <GB> --ha-replicas 2 --explain
```

<paste --explain output here>

### Topology BOM

```
python3 scripts/size.py topology \
  --deployment-type <containerized|ocp> --topology <name> \
  --managed-hosts <N> --concurrent-jobs <N> --format md
```

<paste output here>

### Component Sizing

```
python3 scripts/size.py component --component controller --concurrent-jobs <N>
python3 scripts/size.py component --component hub --managed-hosts <N>
python3 scripts/size.py component --component eda
```

<paste output here>

### OCP Pod Specs _(OCP only)_

```
python3 scripts/size.py ocp-pods --format yaml
```

<paste output + any engagement-specific adjustments here>

## 4. Component Sizing Detail

<Repeat key table from quick reference with narrative explaining each component's driver.>

## 5. Automation Mesh Design

<Describe node placement, peering topology, hop node rationale if any.
Reference references/node-sizing.md rules used.>

## 6. Growth Path

| Horizon | Action | Result |
|---|---|---|
| Now | <baseline topology> | <capacity> |
| +<N> hosts / +<N> jobs | Add <N> execution nodes | <new capacity> |
| 2× scale | <next step: vertical or horizontal> | <new capacity> |
| OCP autoscaling | <HPA + node autoscaler config if OCP> | Dynamic |

## 7. Cost (Indicative, <date>)

<Use cost-model.md template. Infrastructure only — no subscription line.>

Total infrastructure: A: ~$<X>/month (<deployment type>, <provider>, <years> amortisation)
AAP subscription: contact Red Hat — see redhat.com/pricing

## 8. Assumptions and Validation Plan

<Copy assumption table from quick reference.>

**Validation plan — before procurement:**
1. Load test: <N> concurrent jobs, forks=<N>, duration=<time>
2. Monitor: AWX `api/v2/metrics` — `awx_running_jobs_total`, `awx_pending_jobs_total`
3. EDA: send synthetic event burst at <N> events/s, verify processing lag < <threshold>
4. Hub: trigger full sync, verify completion within maintenance window
5. DB: project growth over 90 days under test load; compare with allocated storage
```
