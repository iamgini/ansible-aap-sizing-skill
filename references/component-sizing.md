# Component Sizing Reference

Per-component resource specifications for AAP 2.6+. OCP pod resource YAML is the known-good
baseline from Red Hat documentation (performance benchmarks). All figures marked `A:` are planning
defaults; measure under real load before final procurement.

---

## Automation Controller

The controller runs the web UI, REST API, task dispatcher, and job runner (via ansible-runner).
On containerized RHEL it runs as systemd services. On OCP it runs as three pods: web, task, redis.

### Containerized RHEL (VM sizing)

| Resource | Minimum | Recommended (production) | Sizing driver |
|---|---|---|---|
| vCPU | 4 | 8+ | Event processing; API request throughput |
| RAM | 16 GB | 32 GB | Job events, API sessions, task queue |
| Disk `/var/lib/awx` | 20 GB | 50 GB | EE container image cache |
| Disk (DB, if co-located) | 40 GB | 200 GB+ | Job history, facts, events |

> For hybrid nodes (control + execution): add execution node RAM on top (1 GB / 10 forks + 2 GB).

### OCP Operator — pod resource baseline

Source: Red Hat AAP performance benchmarks (AAP 2.6 Optimization Guide, May 2026).

```yaml
# Automation Controller — task pod (runs ansible-runner, job dispatch)
task_resource_requirements:
  requests:
    cpu: "1000m"
    memory: "8Gi"
  limits:
    cpu: "4000m"
    memory: "8Gi"

# Automation Controller — web pod (REST API, UI)
web_resource_requirements:
  requests:
    cpu: "500m"
    memory: "1.5Gi"
  limits:
    cpu: "2000m"
    memory: "1.5Gi"

# Redis (session cache, celery broker)
redis_resource_requirements:
  requests:
    cpu: "250m"
    memory: "1.5Gi"
  limits:
    cpu: "500m"
    memory: "1.5Gi"

# Execution Environment pod (Container Group — per-job pod)
ee_resource_requirements:
  requests:
    cpu: "100m"
    memory: "400Mi"
  limits:
    cpu: "500m"
    memory: "400Mi"
```

> **OCP note:** Container Group pods are ephemeral — one pod per running job. Size the OCP worker
> node pool to accommodate peak concurrent job pods. At 30 concurrent jobs:
> `30 × (100m CPU + 400Mi RAM) = 3 vCPU + 12 GiB RAM` minimum for EE pods alone.

---

## Private Automation Hub

Hub provides a self-hosted Ansible content repository (collections, EEs, roles) using Pulp as the
backend. Components: API server, Pulp worker(s), Pulp content server, Redis, managed PostgreSQL.

### Containerized RHEL (VM sizing)

| Resource | Minimum | Recommended | Sizing driver |
|---|---|---|---|
| vCPU | 4 | 8 | Pulp worker throughput; API concurrency |
| RAM | 16 GB | 32 GB | Pulp worker processes; content server cache |
| Disk (content store) | 60 GB | 500 GB+ | Collection, EE image, and role storage |
| Disk (DB) | 20 GB | 100 GB+ | Pulp metadata, sync task history |

> Hub storage is the primary unknown. Run a test sync and measure actual footprint before sizing.
> See storage formula in `references/node-sizing.md §4`.

### OCP Operator — pod resource baseline (A: planning estimates)

```yaml
# Hub API pod
hub_api_resource_requirements:
  requests:
    cpu: "250m"
    memory: "512Mi"
  limits:
    cpu: "1000m"
    memory: "2Gi"

# Pulp worker pod (one or more; scale for sync throughput)
pulp_worker_resource_requirements:
  requests:
    cpu: "250m"
    memory: "512Mi"
  limits:
    cpu: "1000m"
    memory: "2Gi"

# Pulp content server pod
pulp_content_resource_requirements:
  requests:
    cpu: "100m"
    memory: "256Mi"
  limits:
    cpu: "500m"
    memory: "1Gi"
```

> A: UNVERIFIED — validate against Red Hat Hub Operator documentation for your version.

---

## Event-Driven Ansible (EDA)

EDA evaluates incoming events against rulebooks using decision environments (DE — container images).
Components: EDA API server, EDA scheduler, decision environment workers, managed PostgreSQL.

### Containerized RHEL (VM sizing)

| Resource | Minimum | Recommended | Sizing driver |
|---|---|---|---|
| vCPU | 2 | 4–8 | Rulebook activation count; events/s throughput |
| RAM | 8 GB | 16–32 GB | Active decision environments (each DE: A: 400 MB–1 GB RAM) |
| Disk | 20 GB | 40 GB | DE container image cache |

### Decision environment (DE) count

```
# A: UNVERIFIED planning formula
de_count = ceil(rulebook_activations × CONCURRENCY_FACTOR)
# CONCURRENCY_FACTOR = A: 1.0 (one DE per activation, but many share a DE image)
de_memory_gb = de_count × avg_de_memory_gb   # avg_de_memory_gb = A: 0.5 GB
```

### Events/s throughput (A: UNVERIFIED)

EDA throughput depends on rulebook complexity and DE startup time. Planning defaults:
- Simple pass-through rules: A: 100–500 events/s per worker
- Complex conditions with API calls: A: 10–50 events/s per worker

> Measure actual event rate from your event sources before sizing EDA workers.

### OCP Operator — pod resource baseline (A: planning estimates)

```yaml
# EDA API pod
eda_api_resource_requirements:
  requests:
    cpu: "250m"
    memory: "512Mi"
  limits:
    cpu: "1000m"
    memory: "1Gi"

# EDA scheduler pod
eda_scheduler_resource_requirements:
  requests:
    cpu: "100m"
    memory: "256Mi"
  limits:
    cpu: "500m"
    memory: "512Mi"
```

---

## AAP Gateway (Platform Gateway — AAP 2.5+)

Gateway is a lightweight reverse proxy providing unified UI, SSO (Keycloak/RHSSO), and common
authentication for all AAP services (Controller, Hub, EDA). Introduced in AAP 2.5.

### Containerized RHEL (VM sizing)

| Resource | Minimum | Recommended | Notes |
|---|---|---|---|
| vCPU | 2 | 4 | Proxy + auth overhead; A: not compute-bound |
| RAM | 4 GB | 8 GB | Session cache, Keycloak JVM heap |
| Disk | 10 GB | 20 GB | Logs, session data |

> Gateway is often co-located with the controller node in smaller deployments. Separate it for
> high-traffic or federated SSO scenarios.

### OCP: Gateway runs as a pod managed by the AAP Operator (A: resource specs TBD per version).

---

## PostgreSQL

AAP uses PostgreSQL for Controller, Hub, and EDA metadata, job history, and content storage.
Can be managed (deployed by the installer) or external (customer-managed, e.g. RDS, Cloud SQL,
Patroni cluster).

### Recommended: External HA PostgreSQL for production

| Resource | Minimum | Recommended | Notes |
|---|---|---|---|
| vCPU | 4 | 8+ | Query throughput scales with job volume |
| RAM | 8 GB | 16–32 GB | Shared buffers (A: 25% of RAM for PostgreSQL) |
| Disk IOPS | 3,000 | 10,000+ | SSD required; IOPS-bound under heavy job load |
| Disk size | 40 GB | Scale with DB growth formula | See `references/node-sizing.md §4` |
| PostgreSQL version | 15 | 15, 16, or 17 | AAP 2.6 requirement |

> For OCP: use an external PostgreSQL cluster. The Operator-managed internal PostgreSQL is not
> recommended for production (no HA, single PVC).

### AAP-specific PostgreSQL settings (A: planning defaults)

```ini
max_connections = 1024        # A: scale with controller replicas
shared_buffers = 4GB          # A: 25% of DB node RAM
work_mem = 64MB               # A: tune per query plan
maintenance_work_mem = 512MB
wal_level = replica           # required for streaming replication
```

---

## Sources

- AAP 2.6 Optimization Guide (PDF, May 2026): https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6/pdfs/aap-optimize-2-6-pdf.pdf
- AAP 2.6 System Requirements: https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6/install-assembly_system_requirements
- Deploying AAP 2 on OpenShift: https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.4/html/deploying_ansible_automation_platform_2_on_red_hat_openshift/
- A: UNVERIFIED figures are planning estimates; validate against your AAP version's documentation and under load.
