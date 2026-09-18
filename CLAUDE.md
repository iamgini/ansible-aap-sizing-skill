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

Every output file opens with a confidence disclaimer table (High / Medium / Low / Indicative).

## Layout

| Path | What |
|---|---|
| `SKILL.md` | Agent workflow spec (interview → topology → calculator → two outputs) |
| `scripts/size.py` | Deterministic calculator: `topology`, `execution-nodes`, `component`, `ocp-pods`, `mesh`, `cost`, `topologies` |
| `references/` | Curated reference files: topology catalog, component sizing, interview, formulas, cost model, output templates, AAP stack overview |
| `example/` | Example engagement outputs |
| `module/` | Lola package structure: `AGENTS.md`, `mcps.json`, `skills/ansible-aap-sizing/SKILL.md` |
| `lola-market.yml` | Lola marketplace registration |
| `.claude/settings.json` | Pre-approves only `python3 scripts/size.py*` — nothing broader |

## Rules

- Every node count, RAM figure, or cost in an output must come from `scripts/size.py` or a quoted
  rule from a `references/` file. No invented numbers.
- Every unknown becomes a stated `A:` default. Never stall waiting for an answer.
- `scripts/size.py` uses Python 3.9+ stdlib only — no external dependencies, no network calls, no
  file writes, no subprocess.
- Output files must open with the confidence disclaimer block from `references/output-templates.md`.
- Figures marked `A:` are planning assumptions. `UNVERIFIED` = no primary-source backing.

## Confidence tiers

| Tier | Meaning |
|---|---|
| **High** | Published Red Hat formula (AAP Planning Guide / Optimization Guide) |
| **Medium** | Formula structure from docs; coefficients estimated — validate under real load |
| **Low** | Not formally documented; planning guess only — measure before procurement |
| **Indicative** | Infrastructure rates only; no subscription pricing |

## Install methods

- **git + symlink**: `ln -s ~/ansible/ansible-aap-sizing-skill ~/.claude/skills/ansible-aap-sizing-skill`
  → skill loads as `ansible-aap-sizing-skill`
- **Lola**: `lola install ansible-aap-sizing-skill` → skill loads as `ansible-aap-sizing`
  (Lola clones to `~/.lola/` and injects into `~/.claude/CLAUDE.md`; does not create `~/.claude/skills/`)

## Credit

Modelled on [red-hat-ai-sizing-skill](https://github.com/toddward/red-hat-ai-sizing-skill) by toddward.
The interview → calculator → two-output-files pattern, skill structure, and reference file layout are
adapted from that project.
