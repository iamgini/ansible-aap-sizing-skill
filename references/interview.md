# AAP Sizing Interview

Use `A:` for every assumed default; repeat each assumption back to the user. Use `UNVERIFIED` when
no primary-source fact is available.

## Interview control

- Ask related questions in rounds; never ask more than about 4 questions in one round.
- Round 1: deployment basics (type, topology, version, components). Round 2: scale (hosts, jobs,
  forks, duration). Round 3: mesh and HA (geography, network, availability, growth). Round 4:
  constraints (hardware, budget, disconnected).
- Skip a question when the opening message already answers it.
- After every round, state the captured answer and every `A:` default you will use; invite
  correction before calculating.
- If the user is not available to confirm, proceed with A: defaults and list them — never stall.
- Do not silently convert "managed hosts" into concurrency. Return a range and confidence flag when
  key traffic inputs remain assumed.

## Question zero — output location (always ask first)

Ask this before starting the interview rounds:

> "Where should I write the output files?
> (default: current directory — I'll create `<engagement>/` there)"

| Field | Value |
|---|---|
| Ask | Where to write the two output files? |
| Default | `./` (current working directory) |
| Why | Consultants keep engagement files in specific folders (`oppty_workarea/`, `client-*/`); writing inside the skill repo is wrong |
| Note | Accept any absolute or relative path. Create `<path>/<engagement>/` with `components/` and `sizing/` sub-folders. |

After the user answers (or skips), confirm: *"Output will be written to `<resolved-path>/<engagement>/`."*

---

## Questions, choices, defaults, and effects

| # | Ask | Multiple-choice options | Default if unknown | Why it changes infrastructure |
|---:|---|---|---|---|
| 1 | What deployment type is required? | Containerized RHEL (new); OCP Operator; both (hybrid); migration from RPM | A: containerized RHEL (greenfield) | Selects installer, topology class, node types, and OCP pod vs VM sizing units. |
| 2 | Which AAP version is the target? | 2.5; 2.6; 2.7 (containerized-only); latest | A: 2.7 (containerized-only, latest stable) | Determines component availability (Gateway in 2.5+), RPM deprecation, and supported RHEL/OCP versions. |
| 3 | Which topology best fits? | growth-a (1 VM, dev/test); growth-b (2–3 VMs, small prod); enterprise-a (5–7 VMs); enterprise-b (10+ VMs, HA); ocp-growth; ocp-enterprise | A: enterprise-a for production; growth-b for pilot | Sets VM count, component placement, and HA posture. |
| 4 | Which AAP components are in scope? | Controller only; Controller + Hub; Controller + EDA; All (Controller + Hub + EDA + Gateway); subset | A: all four components (Controller, Hub, EDA, Gateway) | Determines which VMs or pods to size and which storage calculations to run. |
| 5 | How many managed hosts (total inventory)? | < 100; 100–500; 500–2,000; 2,000–10,000; > 10,000; unknown | A: 500 managed hosts; mark low confidence | Sets DB storage growth rate and determines topology floor. |
| 6 | What is the peak concurrent job count? | < 10; 10–30; 30–100; 100–300; > 300; measured trace available | A: 10% of managed hosts / 10 (Little's law estimate); mark as assumed | Primary driver for execution node count and RAM sizing. Measured `awx_running_jobs` metric preferred. |
| 7 | What forks value is used in job templates / `ansible.cfg`? | Default 5; 10; 25; 50; 100; custom; unknown | A: 5 (Ansible default); mark low confidence | Directly determines RAM per execution node (1 GB / 10 forks + 2 GB). |
| 8 | What is the typical job duration at p50/p95? | < 1 min; 1–5 min; 5–30 min; 30–120 min; > 2 h; unknown | A: 10 min p50 (UNVERIFIED); mark assumed | Affects job queue depth and autoscaling responsiveness; long jobs increase peak concurrency. |
| 9 | Is Automation Mesh needed for remote or edge sites? | Single site, no mesh; 2–5 sites; 5–20 sites; edge (100+ sites); unknown | A: single site, no hop nodes | Determines hop node count and receptor peering topology. Multi-site adds significant complexity. |
| 10 | Are there network constraints between sites or to managed hosts? | Open network; firewall (inbound blocked); air-gapped / disconnected; DMZ/segmented; unknown | A: open network; note if inbound blocked (hop node required) | Inbound-blocked networks require hop nodes. Air-gapped requires mirror setup and offline installer. |
| 11 | What HA tier is required? | Dev/test (none); production (N+1 execution nodes); full HA (N+1 all components); multi-zone/site | A: production N+1 for execution nodes; single-instance control | Sets HA_REPLICAS_MIN and determines enterprise-b vs enterprise-a topology. |
| 12 | What is the growth horizon? | 6 months; 1 year; 3 years; 5 years | A: 2-year demand view; scale in 2× increments | Determines initial provisioning headroom and expansion path. |
| 13 | What existing hardware or OCP cluster is available? | Exact VM inventory (vCPU/RAM/disk); OCP cluster specs (worker count/shape); cloud instance types; no preference; unknown | A: no sunk-hardware constraint; greenfield sizing | Bounds topology to available resources; may force topology up or down. |
| 14 | What is the subscription tier and budget boundary? | Standard; Premium; not yet purchased; fixed capex; monthly opex limit; unknown | A: present good/better/best; cost marked UNVERIFIED | Affects support SLA, managed services eligibility, and infrastructure trade-off decisions. |
| 15 | Is this a disconnected / air-gapped installation? | No (internet access); partially disconnected; fully air-gapped | A: connected (internet access available) | Air-gapped installs require: offline installer bundle, local container registry, Hub as the only collection source, and execution environment image mirroring. |

## Restate before calculating

Use this compact confirmation block after Round 2:

```markdown
I will size `<deployment type>` AAP `<version>` using topology `<name>` for `<managed hosts>` managed
hosts and `<concurrent jobs>` peak concurrent jobs at `<forks>` forks.
Measured inputs: `<list any measured values>`.
A: assumed inputs: `<concurrent jobs, forks, job duration, hub storage, DB growth rate, etc.>`.
Components in scope: `<controller, hub, eda, gateway, db>`.
HA posture: `<N+1 execution nodes / full HA / dev-only>`.
Growth horizon: `<N years>`.
I will report normal and failure capacity separately. Correct any assumption before I continue.
```

## Questions to skip

- Skip exact playbook content, role names, and inventory structure — they do not change node sizing.
- Skip team names and project names as proxies for load — ask for job counts and host counts instead.
- Skip "do you need RBAC?" — AAP always has RBAC; it does not change node sizing.
- Skip AAP UI preference questions (dark mode, SSO provider brand) — not infrastructure decisions.
- Skip exact managed host OS distribution unless the question is about connection method (WinRM vs SSH
  vs network device) — connection method affects EE image selection, not node count.

## Sources

- AAP 2.6 Planning Guide: https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6/html/planning_your_installation/
- AAP Optimization Guide: https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6/pdfs/aap-optimize-2-6-pdf.pdf
- techbeatly Ansible Capacity Planning: https://techbeatly.com/ansible-capacity-planning/
