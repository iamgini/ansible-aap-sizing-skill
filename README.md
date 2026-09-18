# ansible-aap-sizing-skill

An [agent skill](https://agentskills.io/specification) that maps an Ansible Automation Platform
deployment request to the infrastructure required: topology selection (growth / enterprise / resilient),
VM or OCP node bill of materials, per-component resource specs (Controller, Private Automation Hub,
Event-Driven Ansible, Gateway, PostgreSQL), Automation Mesh design (control / hybrid / execution / hop
nodes), OCP Operator pod resource requests/limits, and indicative cost — for Red Hat Ansible Automation
Platform on containerized RHEL or OCP Operator. Every engagement produces two files: a one-page
quick reference (topology first) and a full sizing report with calculator trace, growth path, and
validation plan.

## Install

**Option 1 — git clone + symlink (recommended, same as the sibling AI sizing skill):**

```bash
# Clone to any folder
git clone https://github.com/gmadappa/ansible-aap-sizing-skill ~/ansible/ansible-aap-sizing-skill
ln -s ~/ansible/ansible-aap-sizing-skill ~/.claude/skills/ansible-aap-sizing-skill   # Claude Code
# Codex / Gemini / Cursor: ~/.agents/skills/ansible-aap-sizing-skill
```

**Option 2 — [Lola](https://github.com/lola-ai/lola) package manager:**

```bash
pip install lola-ai
lola market add aap-sizing https://raw.githubusercontent.com/iamgini/ansible-aap-sizing-skill/main/lola-market.yml
lola install ansible-aap-sizing-skill -a claude-code --scope user
```

> **How Lola installs:** Lola clones the repo to `~/.lola/` and injects the module instructions
> into `~/.claude/CLAUDE.md` — it does **not** create a directory in `~/.claude/skills/`.
> This is expected; the skill will appear as `ansible-aap-sizing` (vs `ansible-aap-sizing-skill`
> for the git+symlink method). Both work — the skill name difference is by design.

Python 3.9+ and stdlib only — no additional dependencies required.

## Layout

| Path | What |
|---|---|
| `SKILL.md` | The workflow the agent follows (interview → topology → calculator → two outputs) |
| `scripts/size.py` | Deterministic calculator: `topology`, `execution-nodes`, `component`, `ocp-pods`, `mesh`, `cost`, `topologies` |
| `references/topology-catalog.md` | Containerized and OCP topology options with VM counts and planning limits |
| `references/node-sizing.md` | Memory/CPU/storage/network formulas per node type |
| `references/component-sizing.md` | Per-component resource specs and OCP pod requests/limits YAML |
| `references/sizing-formulas.md` | Sourced sizing math (forks → RAM, execution units, DB growth, EDA, Hub storage) |
| `references/interview.md` | 15 candidate questions in 4 rounds with defaults |
| `references/redhat-aap-stack.md` | AAP components, deployment modes, Automation Mesh node types, supported platforms |
| `references/cost-model.md` | Indicative on-prem and cloud infrastructure cost (no subscription prices) |
| `references/output-templates.md` | Quick reference and sizing report output skeletons |
| `example/` | Example engagement outputs (component profiles, calculator JSON, quick reference, sizing report) |

## Try the calculator directly

```bash
# List available subcommands
python3 scripts/size.py --help

# Size execution nodes for 50 concurrent jobs at forks=10, 32 GB nodes
python3 scripts/size.py execution-nodes --concurrent-jobs 50 --forks 10 --ram-per-node 32 --explain

# Show topology BOM for enterprise containerized deployment
python3 scripts/size.py topology --deployment-type containerized --topology enterprise-b \
  --managed-hosts 2000 --concurrent-jobs 50 --format md

# Show OCP pod resource baseline YAML
python3 scripts/size.py ocp-pods --format yaml
```

All figures are labelled planning estimates. Always validate with a load test before procurement.

## Calculation confidence

Not all sizing figures are equally reliable. Every generated output file includes this table:

| Section | Confidence | Basis |
|---|---|---|
| Execution node RAM: `ceil(forks/10) + 2 GB` | **High** | Published formula — Red Hat AAP Planning Guide |
| Execution node count (capacity units) | **High** | Published formula — Red Hat AAP Planning Guide |
| OCP pod requests/limits YAML | **High** | Benchmarked baselines — Red Hat AAP Optimization Guide |
| Topology VM shapes (vCPU / RAM / disk) | **High** | Red Hat AAP Planning Guide + `ansible/test-topologies` |
| DB storage growth estimate | **Medium** | Formula structure from docs; coefficients are estimated — measure under real load |
| Hub storage estimate | **Medium** | No official formula exists — community-derived; measure after first sync |
| EDA sizing (activations, events/s) | **Low** | Not formally documented by Red Hat; planning guess only — measure before procurement |
| Cost | **Indicative** | Infrastructure rates only (dated); no subscription pricing — contact Red Hat |

`A:` in any output = assumption; `UNVERIFIED` = no primary-source backing.
**Replace all `A:` values with measured telemetry before ordering hardware.**

## Trust and transparency

When you use this skill, your AI agent will run `scripts/size.py` to produce traceable sizing
numbers. Here is exactly what that script does and does not do:

| | What the script does |
|---|---|
| ✅ | Pure arithmetic — applies formulas from `references/sizing-formulas.md` to your inputs |
| ✅ | Prints results to stdout (markdown, JSON, or YAML) |
| ✅ | Python 3.9+ **standard library only** — no pip packages, no external dependencies |
| ❌ | **No network calls** of any kind (no HTTP, no DNS, no socket) |
| ❌ | **No file writes** unless you explicitly redirect output (`> file.json`) |
| ❌ | **No shell execution**, no subprocess, no system calls |
| ❌ | **No telemetry**, no analytics, no data sent anywhere |

**Read it yourself before approving:**

```bash
cat scripts/size.py          # ~300 lines, plain Python
```

**Use `--dry-run` to see the formula before the calculation runs:**

```bash
python3 scripts/size.py execution-nodes --concurrent-jobs 50 --forks 10 --ram-per-node 32 --dry-run
```

**What the `.claude/settings.json` in this repo pre-approves:**

```json
"allow": [
  "Bash(python3 scripts/size.py*)"
]
```

Only `size.py` calls are pre-approved — nothing broader. If your agent asks to run
anything else from this repo, deny it and open an issue.

## Credit

Inspired by [red-hat-ai-sizing-skill](https://github.com/toddward/red-hat-ai-sizing-skill) by toddward. The interview → calculator → two-output-files pattern, skill structure, and reference file layout are adapted from that project.
