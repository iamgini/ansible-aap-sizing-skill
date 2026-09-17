# AAP Topology Catalog

Use `A:` for every assumed default. Cross-check with the official
[ansible/test-topologies](https://github.com/ansible/test-topologies) repository for reference
inventory files and validated component placements.

> **AAP 2.7+ note:** RPM-based installer is deprecated from AAP 2.5 and removed in AAP 2.7.
> All new deployments use the containerized installer (RHEL) or OCP Operator. Plan migrations
> accordingly.

---

## Containerized RHEL Topologies

### `growth-a` — All-in-one (1 VM)

| Attribute | Value |
|---|---|
| VM count | 1 |
| Components | Controller + Hub + EDA + Gateway + managed PostgreSQL (all on one host) |
| Min vCPU | 4 |
| Min RAM | 16 GB (32 GB if seeding Hub collections: `hub_seed_collections=true`) |
| Min disk | 60 GB total; 20 GB `/var/lib/awx` |
| Use case | Development, proof-of-concept, lab, demo |
| Managed hosts | Up to ~50 (A: planning limit) |
| Concurrent jobs | Up to ~10 (A: planning limit) |
| HA | None |
| Reference | `ansible/test-topologies` `cont-a.env-a` |

**When to use:** Internal dev/test only. Not for production. Single point of failure.

---

### `growth-b` — Separated database (2–3 VMs)

| Attribute | Value |
|---|---|
| VM count | 2–3 |
| Components | VM1: Controller + Hub + EDA + Gateway; VM2: PostgreSQL (external managed DB) |
| Optional | VM3: dedicated execution node |
| Min vCPU per VM | 4 (controller VM), 4 (DB VM) |
| Min RAM per VM | 16 GB (controller VM), 8 GB (DB VM) |
| Min disk | 60 GB controller; 100 GB DB (A: scales with job volume) |
| Use case | Small production, pilot, single-site |
| Managed hosts | Up to ~200 (A: planning limit) |
| Concurrent jobs | Up to ~20 (A: planning limit) |
| HA | None (DB single instance) |
| Reference | `ansible/test-topologies` `cont-b.env-a` |

**When to use:** First production deployment. Simple to operate. No redundancy — plan for growth-b
→ enterprise-a migration.

---

### `enterprise-a` — Separated components (5–7 VMs)

| Attribute | Value |
|---|---|
| VM count | 5–7 |
| Components | Control node(s) · Execution node(s) · Private Automation Hub · EDA · Gateway · PostgreSQL |
| Min vCPU per control VM | 4–8 |
| Min RAM per control VM | 16 GB |
| Min vCPU per execution VM | 8 (A: scales with forks; 1 GB RAM / 10 forks + 2 GB) |
| Min RAM per execution VM | 16–32 GB (A: depends on concurrent jobs × forks) |
| Min disk | 20 GB `/var/lib/awx` per execution/control VM; 200 GB+ Hub storage (A: depends on collections) |
| Use case | Production, medium scale, single-site |
| Managed hosts | 200–2,000 (A: planning range) |
| Concurrent jobs | 20–100 (A: planning range) |
| HA | Basic (manual failover); consider enterprise-b for production HA |
| Reference | `ansible/test-topologies` `cont-a.env-b` |

**When to use:** Standard production for most organizations. Separation of control and execution
planes allows independent scaling.

---

### `enterprise-b` — Resilient / HA (10+ VMs)

| Attribute | Value |
|---|---|
| VM count | 10+ |
| Components | 2+ control nodes · 2+ execution nodes · Hub (clustered) · EDA (clustered) · Gateway · PostgreSQL HA (A: external HA DB e.g. Patroni/RDS) |
| Min vCPU per control VM | 8 |
| Min RAM per control VM | 32 GB |
| Min vCPU per execution VM | 8–16 |
| Min RAM per execution VM | 32–64 GB (A: sized to concurrent jobs × forks + HA reserve) |
| Disk | 20 GB `/var/lib/awx`; Hub 500 GB+ (A: depends on org collection footprint) |
| Use case | Large enterprise, multi-team, production HA, 24×7 |
| Managed hosts | 2,000+ (A: no hard ceiling; scale execution nodes) |
| Concurrent jobs | 100+ (A: scale execution nodes) |
| HA | N+1 execution nodes; active/active control; HA DB |
| Reference | `ansible/test-topologies` `cont-b.env-b` |

**When to use:** Mission-critical production. Scale execution nodes horizontally as job load grows;
scale control nodes vertically for event processing throughput.

---

## OCP Operator Topologies

> **OCP note:** On OpenShift, the AAP Operator manages Controller, Hub, and EDA as pods. Standalone
> execution nodes are replaced by **Container Groups** (Kubernetes pods launched on demand). Only
> **execution** and **hop** nodes can be added externally — control and hybrid node types are not
> supported on OCP Operator deployments.

### `ocp-growth` — Single namespace, minimal

| Attribute | Value |
|---|---|
| OCP worker nodes | 3 (shared with other workloads) |
| Worker node shape | A: 4 vCPU / 16 GiB RAM each |
| Namespace | Single namespace for all AAP components |
| Components | Controller · Hub · EDA · Gateway (all as Operator-managed pods) |
| PostgreSQL | Managed by Operator (internal) or external |
| Container Groups | Default container group for job execution |
| Use case | Dev, pilot, single-team OCP deployment |
| Concurrent jobs | Up to ~20 (A: limited by node capacity) |
| HA | Pod-level restart only; no multi-replica |
| Reference | `ansible/test-topologies` `ocp-a.env-a` |

**When to use:** Getting started on OCP, evaluating AAP Operator. Not production HA.

---

### `ocp-enterprise` — Multi-namespace, HA

| Attribute | Value |
|---|---|
| OCP worker nodes | 3+ dedicated AAP worker nodes (A: separate from general workloads) |
| Worker node shape | A: 8 vCPU / 32 GiB RAM each (scale up as job load grows) |
| Namespace | Dedicated namespace(s) per AAP component or environment |
| Components | Controller · Hub · EDA · Gateway (all HA replicas) |
| PostgreSQL | External HA PostgreSQL (A: recommended for production) |
| Container Groups | Multiple container groups (prod/dev/isolated) with resource quotas |
| External execution nodes | Optional: RHEL execution nodes peered via Automation Mesh |
| Use case | Production OCP deployment, multi-team, 24×7 |
| Concurrent jobs | Scales with worker node pool; add nodes to increase capacity |
| HA | Multi-replica pods; node anti-affinity; external DB HA |
| Reference | `ansible/test-topologies` `ocp-b.env-a` |

**When to use:** Production AAP on OpenShift. Size worker nodes based on peak pod resource usage
(see `references/component-sizing.md` for pod requests/limits).

---

## Choosing a Topology — Decision Table

| Scale | Deployment | HA needed? | Topology |
|---|---|---|---|
| Dev/test | RHEL | No | `growth-a` |
| Small prod (< 200 hosts) | RHEL | No | `growth-b` |
| Medium prod (200–2000 hosts) | RHEL | Basic | `enterprise-a` |
| Large prod (2000+ hosts) | RHEL | Full HA | `enterprise-b` |
| Dev/pilot | OCP | No | `ocp-growth` |
| Production | OCP | Yes | `ocp-enterprise` |

## Sources

- Red Hat AAP 2.6 Planning Guide: https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6/html/planning_your_installation/
- ansible/test-topologies: https://github.com/ansible/test-topologies
- AAP 2.6 System Requirements: https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6/install-assembly_system_requirements
