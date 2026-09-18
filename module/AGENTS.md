# Ansible AAP Sizing Skill

Module provides a skill for sizing Red Hat Ansible Automation Platform (AAP) deployments —
containerized RHEL or OCP Operator — following Red Hat official documentation and community
best practices.

## When to Use

### Skills

- **ansible-aap-sizing skill**: Use the `ansible-aap-sizing` skill to map an AAP deployment
  request to infrastructure: topology selection (growth / enterprise / resilient), VM or OCP
  node bill of materials, Automation Mesh design (control / hybrid / execution / hop nodes),
  per-component resource specs (Controller, Hub, EDA, Gateway, PostgreSQL), OCP Operator pod
  requests/limits, and indicative cost.
  Invoke when asked about "how many nodes", "what hardware for N managed hosts",
  "right-size AAP", "containerized vs OCP Operator", "how many execution nodes",
  "size EDA", "AAP on OpenShift resource limits", or any AAP topology question.

## Configuration

**Required Dependencies:**

- `python3` (3.9+) — Used by `scripts/size.py` to run the deterministic sizing calculator
- No external pip packages; standard library only

**Security:** The calculator (`scripts/size.py`) makes no network calls, writes no files
unless you redirect output, and uses only Python stdlib. `.claude/settings.json` pre-approves
only `python3 scripts/size.py*` — nothing broader.

## Notes

- Every generated output file carries a confidence disclaimer (High / Medium / Low) per section
- Figures marked `A:` are assumptions; replace with measured telemetry before procurement
- Inspired by [red-hat-ai-sizing-skill](https://github.com/toddward/red-hat-ai-sizing-skill)
