---
name: ansible-aap-sizing
description: >-
  Size Red Hat Ansible Automation Platform (AAP) deployments — maps a use case to topology,
  node bill of materials, Automation Mesh design, component resource specs (Controller, Hub,
  EDA, Gateway, PostgreSQL), OCP Operator pod requests/limits, and indicative cost.
  Covers containerized RHEL and OCP Operator for AAP 2.6 and 2.7.
user-invocable: false
triggers:
  - "how many nodes do we need"
  - "what hardware for managed hosts"
  - "right-size aap"
  - "size aap"
  - "aap sizing"
  - "containerized vs ocp operator"
  - "how many execution nodes"
  - "size eda"
  - "aap on openshift resource limits"
  - "automation platform topology"
  - "growth topology"
  - "enterprise topology"
  - "size ansible automation platform"
  - "aap infrastructure"
  - "execution node sizing"
---


# AAP deployment → infrastructure mapper

Input: an engagement description ("size AAP for 500 managed hosts, 30 concurrent jobs, on OCP").
Output, always: **two files plus a chat summary**.

1. `<engagement>-quick-reference.md` — topology first (name, deployment type, VM/node count), then
   the node BOM, Automation Mesh design, per-component resource specs, OCP pod YAML (if OCP),
   concurrency envelope, assumptions, what saturates first.
2. `<engagement>-sizing-report.md` — the same decisions with the reasoning: topology selection
   rationale, calculator trace, component sizing detail, growth path, indicative cost, assumptions
   and a validation plan.

Four rules — they are what a reviewer checks first:

- **Every number is traceable.** Node counts, RAM, vCPU, storage, pod requests/limits, and cost
  come from `scripts/size.py` or are quoted rules from `references/` files. When a figure comes
  from a written rule (e.g. "20 GB minimum for `/var/lib/awx`"), quote the rule and its source next
  to the number. Keep the `--explain` trace / JSON.
- **Every topology pick comes from `references/topology-catalog.md`**, cross-checked against the
  official `ansible/test-topologies` reference topologies, and carries a rationale blurb.
- **Every unknown becomes a stated default** (`A:` marker, from `references/interview.md` defaults),
  echoed back to the user in both outputs. Ask only questions whose answer changes the infrastructure.
  If the user is unavailable, proceed on defaults and list them — never stall.
- **Specs, prices and dates carry sources.** Cost is always "indicative, <date>".

## When NOT to use

- Pure AAP performance benchmarking / load-testing requests — this skill *plans*, not measures.
- Pre-installation network firewall / security policy design — note it is out of scope.
- Hosted / managed AAP-as-a-service decisions only (no self-hosting) — the sizing machinery is
  unnecessary; point to Red Hat pricing pages.

## Workflow

`SKILL` = the directory containing this file; every path below is relative to it.

### 0. Output location — ask first, before anything else

Before the interview, ask one question:

> "Where should I write the output files?
> (default: current directory — I'll create `<engagement>/` there)"

Accept a path or just Enter for the current directory. Store it as `OUTPUT_DIR`.
Create `OUTPUT_DIR/<engagement>/` with sub-folders `components/` and `sizing/`.
All output files go there. Never write inside the skill's own directory.

If the user is unavailable or does not respond, default to the current working directory
and state it as `A: output written to ./`.

### 1. Classify the deployment

Map the request onto one or more deployment classes:

| Class | Key | Description |
|---|---|---|
| Greenfield containerized | `greenfield-containerized` | New AAP on RHEL using containerized installer |
| Greenfield OCP Operator | `greenfield-ocp` | New AAP deployed via OCP OperatorHub |
| Migration RPM → containerized | `migration-rpm-to-containerized` | Existing RPM-based AAP migrating to containers |
| Scale existing | `scale-existing` | Adding capacity to an existing AAP cluster |
| Add EDA | `add-eda` | Adding Event-Driven Ansible to an existing deployment |
| Add Hub | `add-hub` | Adding Private Automation Hub to an existing deployment |
| Hybrid mesh | `hybrid-mesh` | Extending Automation Mesh to remote/edge sites |

Mixed engagements are normal — classify each tier separately, then combine.

### 2. Interview — only decision-changing questions

Follow `references/interview.md`: 15 candidate questions grouped in rounds of ≤4. Skip anything
the opening message already answers. Core set: deployment type · topology target · AAP version ·
components in scope · managed host count · peak concurrent jobs · forks setting · job duration ·
geographic distribution · network constraints · HA requirements · growth horizon · existing
hardware / OCP cluster specs · budget/subscription boundary · disconnected install. "I don't know"
→ profile default, marked `A:`. After each round restate answers + defaults in one short block.

Record everything in an **Engagement brief** table (§1 of the report).

### 3. Select topology

Read `references/topology-catalog.md`. Map the request onto a named topology:

- **Containerized RHEL:** `growth-a` (1 VM, dev/test) · `growth-b` (2–3 VMs) · `enterprise-a`
  (5–7 VMs) · `enterprise-b` (10+ VMs, HA)
- **OCP Operator:** `ocp-growth` (single namespace, minimal) · `ocp-enterprise` (multi-namespace, HA)

Cross-check with the `ansible/test-topologies` GitHub repository for the matching reference
inventory. Write the topology rationale blurb: why this topology, trade-off vs the runner-up.

### 4. Size — the calculator does the math

```bash
# Show topology VM/node BOM
python3 $SKILL/scripts/size.py topology \
    --deployment-type containerized|ocp \
    --topology growth-a|growth-b|enterprise-a|enterprise-b|ocp-growth|ocp-enterprise \
    --managed-hosts <N> --concurrent-jobs <N> [--format md] [--explain]

# Size execution nodes from concurrent jobs and forks
python3 $SKILL/scripts/size.py execution-nodes \
    --concurrent-jobs <N> --forks <N> --ram-per-node <GB> [--ha-replicas 2] [--format md] [--explain]

# Per-component resource sizing
python3 $SKILL/scripts/size.py component \
    --component controller|hub|eda|gateway|db \
    [--concurrent-jobs <N>] [--managed-hosts <N>] [--format md]

# OCP pod resource requests/limits baseline YAML
python3 $SKILL/scripts/size.py ocp-pods [--format yaml|md|json]

# Automation Mesh node design
python3 $SKILL/scripts/size.py mesh \
    --execution-nodes <N> [--sites <N>] [--hop-nodes <N>] [--format md]

# Indicative cost
python3 $SKILL/scripts/size.py cost \
    --nodes <N> --deployment-type containerized|ocp [--provider on-prem|aws|azure|gcp]
```

How to read a run:
- `binding_constraint` / `what_saturates_first`: memory (RAM for forks) · CPU (event processing) ·
  storage (Hub sync, DB growth) · network (mesh fabric). That is the answer to "what saturates first".
- The **sensitivity block** is the honest answer — quote the range, not the point.
- **Reserves already inside the number:** the 1.30 burst reserve on concurrent jobs, the 0.20 headroom,
  and `--ha-replicas 2` (≥2 execution nodes). **Not inside:** rolling-update capacity (+1 node), one-
  node-down capacity, and growth. State which you added.
- On OCP: `container_group` execution (Kubernetes pods) replaces standalone execution nodes — size
  the worker node pool instead. The calculator notes this when `--deployment-type ocp` is set.
- Run every finalist topology at the requested scale; then explore levers only for the leading option.
  **Levers, cheapest first:** increase RAM/vCPU on existing nodes → add execution nodes → split
  control and execution planes → add hop nodes for remote sites → OCP autoscaling.

### 5. Node, host, storage, network

`size.py component` gives the per-component resource recommendations. Use
`references/node-sizing.md` for the storage and network rules, and `references/component-sizing.md`
for per-service resource specs and OCP pod YAML baselines. For the AAP stack overview (component
roles, supported OCP/RHEL versions, key operators), see `references/redhat-aap-stack.md`.

The BOM lists:
- **Containerized:** all VM roles (controller/hybrid/execution/hop/hub/eda/db) as separate lines
- **OCP:** platform worker nodes for AAP pods + any external execution or hop nodes

### 6. Cost — indicative, dated

`size.py cost` + `references/cost-model.md`: on-prem 3/5-yr amortised $/month, cloud on-demand and
reserved $/month, OCP worker node cost. Never invent subscription prices — always state "contact Red
Hat account team or see redhat.com/pricing". Cite the infrastructure price source and date.

### 7. Write the two outputs + chat summary

**Every output file must open with the confidence disclaimer from `references/output-templates.md`.**
The disclaimer table has three confidence levels — High (published Red Hat formula), Medium
(derived/community), Low (unverified planning guess). Fill it accurately for the sections actually
present in this engagement. Never omit it; a reader picking up the file cold must know immediately
which numbers to trust and which to validate.

Fill `references/output-templates.md` exactly (its section order wins). Quick reference: topology
first → node BOM → Automation Mesh → component specs → OCP pod YAML (if OCP) → concurrency envelope
(peak concurrent jobs, forks capacity, event rate, what saturates) → assumptions → validation gate.
Report: engagement brief, topology rationale, calculator trace, component sizing, mesh design, growth
path, cost, **Assumptions & validation plan** (load test at target concurrent job count and fork depth
before procurement). Finish with a 6–10 line chat summary: topology answer, key component specs, the
two biggest assumptions, the next validation step.

## Quick reference

| Need | Use |
|---|---|
| Topology options with VM counts and use cases | `references/topology-catalog.md` |
| Which questions, in what order, with defaults | `references/interview.md` |
| Memory/CPU/storage formulas, sourced | `references/sizing-formulas.md` |
| Per-component resource specs and OCP pod YAML | `references/component-sizing.md` |
| Node/storage/network rules | `references/node-sizing.md` |
| AAP component roles, versions, operators | `references/redhat-aap-stack.md` |
| Cost formulas and dated defaults | `references/cost-model.md` |
| Output file skeletons | `references/output-templates.md` |
| Calculator subcommands | `scripts/size.py <sub> --help` |

## Red flags — stop and fix

- A node count, RAM figure, or $ figure in your draft that did not come out of `size.py` or a quoted rule.
- A topology chosen without checking `references/topology-catalog.md` and the `test-topologies` reference.
- Forks not converted to RAM (the 1 GB / 10 forks + 2 GB rule — missing this underestimates by 30–50%).
- OCP pod resource limits left unset (unbounded pods get evicted under node pressure).
- EDA sized without decision environment count, rulebook activation count, and events/s throughput.
- Private Automation Hub sized without collection sync scope, mirror depth, and storage calculation.
- Automation Mesh hop nodes omitted when remote sites or restricted networks are mentioned.
- Cost shown without a date and source, or a subscription price invented rather than deferred to Red Hat.
- One of the two output files missing, or the quick reference not leading with topology.

## Common mistakes

| Mistake | Fix |
|---|---|
| Asking all 15 interview questions at once | Round 1 covers deployment type, topology, scale, components — default the rest with `A:` |
| Total managed hosts → concurrency by a guessed % | Use the `execution-nodes` subcommand with measured peak concurrent jobs; flag for telemetry |
| Treating "execution nodes" the same on OCP and RHEL | On OCP, Container Groups (pods) replace execution nodes — size the worker node pool |
| Sizing forks at the system maximum (512) | Size at the forks value set in job templates or `ansible.cfg` — ask if unknown, default to `A: 5` |
| "Fits in RAM" = done | Check CPU for event processing throughput and storage for DB growth at job volume |
| One-size Hub storage | Hub storage = collections × avg_size × mirrors + sync overhead — ask sync scope |
| Treating on-prem list prices as facts | Planning defaults / indicative only; use the quote in hand and label it |
