# Red Hat Ansible Automation Platform — Stack Overview

Reference for the agent: component roles, deployment modes, supported platforms, key operators,
and collections. Use to answer "what does this component do?" and "is this supported?" questions.

---

## AAP Components (2.5+)

AAP 2.5 introduced the **Platform Gateway** as a unified entry point, consolidating all four
components under one URL and SSO layer.

| Component | Role | Port | Notes |
|---|---|---|---|
| **Platform Gateway** | Unified UI, reverse proxy, SSO (Keycloak/RHSSO), common auth | 443 (HTTPS) | Introduced in AAP 2.5. Required in 2.5+. |
| **Automation Controller** | Job scheduling, RBAC, REST API, workflow engine, credential management | 443 (via Gateway) | Previously "AWX" / "Tower". Core of AAP. |
| **Private Automation Hub** | Self-hosted collection repository (Pulp), EE registry, content signing | 443 (via Gateway) | Replaces direct Galaxy access. Required for air-gapped. |
| **Event-Driven Ansible (EDA)** | Rulebook-based event processing, integration with EDA Controller | 443 (via Gateway) | Added in AAP 2.4. Uses decision environments. |
| **Automation Mesh** | Receptor-based overlay network connecting all node types | TCP (receptor) | Not a separate UI; integrated into Controller. |

### Component dependencies

```
Internet / managed hosts
        ↓
  [Platform Gateway]  ← SSO / unified UI
    ↙      ↓      ↘
[Controller] [Hub] [EDA]
        ↓             ↓
  [Automation Mesh]  [Decision Environments]
        ↓
  [Execution Nodes / Container Groups]
        ↓
  [Managed Hosts]
```

---

## Deployment Modes

| Mode | Installer | Supported since | Status in 2.7 |
|---|---|---|---|
| **Containerized RHEL** | `ansible-installer` (container-based) | AAP 2.4 | **Recommended** |
| **RPM on RHEL** | Legacy RPM installer | AAP 1.x–2.5 | **Deprecated** (removed in 2.7) |
| **OCP Operator** | AAP Operator via OperatorHub | AAP 2.1 | Supported |
| **Managed cloud** | ROSA (AWS), ARO (Azure), OCP on GCP | AAP 2.4+ | Supported |

> **AAP 2.7+:** Only containerized RHEL and OCP Operator are supported. Plan RPM migrations before
> upgrading to 2.7.

---

## Automation Mesh — Node Types

| Node type | Runs jobs? | Sizing driver | OCP Operator support |
|---|---|---|---|
| **Control** | No (cluster jobs only) | CPU for event processing | Not supported on OCP |
| **Hybrid** | Yes + cluster jobs | RAM (forks) + CPU (events) | Not supported on OCP |
| **Execution** | Yes (user jobs only) | RAM (forks) | Supported (added externally) |
| **Hop** | No (relay/routing) | Minimal; network-bound | Supported (added externally) |

> On OCP Operator: the Controller pod acts as the control plane. External execution and hop nodes
> connect via receptor. Container Groups (Kubernetes pods) replace standalone execution nodes.

### Container Groups (OCP)

- Default execution mechanism on OCP Operator deployments
- One Kubernetes pod per running job (ephemeral, from EE image)
- Job pods run in the AAP namespace by default; can target other namespaces or clusters
- Size the OCP worker node pool for peak concurrent job pod demand

---

## Supported Platforms

### RHEL (Containerized Installer)

| RHEL Version | Architecture | AAP 2.6 | AAP 2.7 |
|---|---|---|---|
| RHEL 9.4+ | x86_64, aarch64, ppc64le, s390x | Supported | Supported |
| RHEL 10+ | x86_64, aarch64 | Supported (2.6+) | Supported |
| RHEL 8.x | x86_64 | Not supported (containerized) | Not supported |

### OpenShift (OCP Operator)

| OCP Version | AAP Operator | Notes |
|---|---|---|
| OCP 4.12+ | AAP Operator 2.4+ | Check operator compatibility matrix |
| OCP 4.16+ | AAP Operator 2.6+ | Recommended for new deployments |

Source: Check [Red Hat Operator Certification](https://catalog.redhat.com/software/operators/) for
the current compatibility matrix for your specific OCP version.

### Managed Cloud

- **ROSA** (Red Hat OpenShift Service on AWS) — OCP Operator supported
- **ARO** (Azure Red Hat OpenShift) — OCP Operator supported
- **GCP Marketplace** — OCP on GCP, OCP Operator supported

---

## Key Operators (OCP)

| Operator | What it manages | Source |
|---|---|---|
| **AAP Operator** | AnsibleAutomationPlatform CR (Controller + Hub + EDA + Gateway) | OperatorHub |
| **EDA Operator** (standalone) | EDA Controller only (for standalone EDA deployments) | OperatorHub |
| **Hub Operator** (standalone) | Private Automation Hub only | OperatorHub |

---

## Key Collections for Configuration as Code (CaC)

| Collection | Use | AAP version |
|---|---|---|
| `infra.aap_configuration` | Configure all AAP components via CaC | 2.5+ |
| `ansible.platform` | Unified platform API resources | 2.5+ |
| `ansible.controller` | Automation Controller CaC | 2.4+ |
| `ansible.hub` | Private Automation Hub CaC | 2.4+ |
| `ansible.eda` | EDA CaC | 2.4+ |

---

## PostgreSQL Requirements

| AAP version | PostgreSQL version |
|---|---|
| AAP 2.4 | PostgreSQL 13 |
| AAP 2.5 | PostgreSQL 13, 15 |
| AAP 2.6 | PostgreSQL 15, 16, 17 |
| AAP 2.7 | PostgreSQL 15, 16, 17 (external recommended for production) |

---

## Sources

- AAP 2.7 Documentation Hub: https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.7
- AAP 2.6 Planning Guide: https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6/html/planning_your_installation/
- AAP 2.5 Automation Mesh (Operator): https://docs.redhat.com/en-us/documentation/red_hat_ansible_automation_platform/2.5/pdf/automation_mesh_for_managed_cloud_or_operator_environments/
- Deploying AAP on OCP: https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.4/html/deploying_ansible_automation_platform_2_on_red_hat_openshift/
- ansible/test-topologies: https://github.com/ansible/test-topologies
