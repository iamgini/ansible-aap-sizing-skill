# CLAUDE.md

This repo is an agent skill for sizing Red Hat Ansible Automation Platform (AAP) deployments —
containerized RHEL or OCP Operator — following the agentskills.io specification.

## What this skill does

Input: an engagement description ("size AAP for 500 managed hosts on OCP").
Output, always: **two files per engagement** written to `<engagement>/`:

1. `<engagement>-quick-reference.md` — topology first, node BOM, component specs, Automation Mesh
   design, concurrency envelope, assumptions, what saturates first.
2. `<engagement>-sizing-report.md` — full reasoning, calculator trace, component sizing, growth path,
   indicative cost, validation plan.

## Layout

| Path | What |
|---|---|
| `SKILL.md` | The workflow the agent follows (interview → calculator → two outputs) |
| `scripts/size.py` | Deterministic calculator: `topology`, `execution-nodes`, `component`, `ocp-pods`, `mesh`, `cost` |
| `references/` | Curated reference files: topology catalog, component sizing, interview, formulas, cost model, output templates, AAP stack overview |
| `example/` | Example engagement outputs |

## Rules

- Every node count, RAM figure, or cost in an output must come from `scripts/size.py` or a quoted
  rule from a `references/` file. No invented numbers.
- Every unknown becomes a stated `A:` default. Never stall waiting for an answer.
- `scripts/size.py` uses Python 3.9+ stdlib only — no external dependencies.

## Credit

Modelled on [red-hat-ai-sizing-skill](https://github.com/toddward/red-hat-ai-sizing-skill) by toddward.
The interview → calculator → two-output-files pattern, skill structure, and reference file layout are
adapted from that project.
