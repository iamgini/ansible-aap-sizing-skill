# TODO

## v1 — Agent Skill (current scope)

- [x] `CLAUDE.md` — project instructions for Claude Code
- [x] `README.md` — install, layout, try-the-calculator
- [x] `SKILL.md` — agent workflow spec (interview → topology → calculator → two outputs)
- [x] `scripts/size.py` — skeleton calculator with working `execution-nodes` subcommand
- [x] `references/topology-catalog.md` — containerized and OCP topology options
- [x] `references/node-sizing.md` — memory/CPU/storage formulas
- [x] `references/component-sizing.md` — per-component resource specs and OCP pod YAML
- [x] `references/interview.md` — 15 candidate questions in 4 rounds
- [x] `references/sizing-formulas.md` — sourced math
- [x] `references/cost-model.md` — indicative cost model
- [x] `references/output-templates.md` — quick reference and sizing report templates
- [x] `references/redhat-aap-stack.md` — AAP component and platform overview
- [x] `example/README.md` — example engagement directory structure
- [ ] Complete `scripts/size.py` `topology`, `component`, `mesh` subcommand implementations
- [ ] Add `scripts/test_size.py` unit tests for core formulas
- [ ] Write a complete example engagement (containerized enterprise, ~500 managed hosts)
- [ ] Write a complete example engagement (OCP Operator, growth topology)
- [ ] Validate all sizing formulas against Red Hat AAP 2.6/2.7 documentation

## v2 — MCP Integration (future)

- [ ] MCP server exposing sizing tools as callable tools:
  - `size_topology` — topology selection and VM BOM
  - `size_execution_nodes` — execution node count from jobs + forks
  - `size_eda` — EDA decision environment sizing from rulebook activations + events/s
  - `size_hub` — Private Automation Hub storage and compute from collection sync scope
  - `size_cost` — indicative infrastructure + subscription cost
- [ ] Live AAP telemetry enrichment: when an existing AAP instance is connected via MCP, pull
  real fork usage, active job counts, node capacities, and event rates to validate/replace `A:` planning
  assumptions with measured data
- [ ] Integration with `aap-mcp-*` servers (`aap-mcp-system-monitoring`, `aap-mcp-job-mgmt`) for
  post-deployment capacity reviews
- [ ] Automated right-sizing recommendations for existing clusters: compare current resource usage
  against sizing model, flag over- or under-provisioned nodes

- [x] Package as a [Lola](https://github.com/lola-ai/lola) module — `module/` structure with
  `AGENTS.md`, `mcps.json`, `skills/ansible-aap-sizing/SKILL.md` and `lola-market.yml` at repo root.
  Lola clones to `~/.lola/` and injects into `~/.claude/CLAUDE.md` (not `~/.claude/skills/`).
  Skill loads as `ansible-aap-sizing` via Lola vs `ansible-aap-sizing-skill` via git+symlink.

## v3 — Stretch Goals

- [ ] Red Hat Customer Portal integration for live subscription pricing lookup (replace indicative
  cost placeholders with current list prices where available)
- [ ] Multi-site / geo-distributed Automation Mesh topology planner: given site locations, latency
  constraints, and managed host distribution, recommend hop node placement and receptor peering
- [ ] EDA rulebook throughput deep-sizing: events/s × rulebook complexity → decision environment
  CPU/memory and activation concurrency model
- [ ] Disconnected / air-gapped install checklist generator alongside the sizing report
- [ ] Comparison mode: given current topology + sizing, model the cost/capacity of migrating to a
  different topology or AAP version
