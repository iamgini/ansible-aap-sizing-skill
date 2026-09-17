# Example Engagements

Each engagement lives in its own folder (kebab-case engagement name).

## Directory layout

```
example/
└── <engagement-name>/
    ├── components/             # Component profile notes (hub storage calc, EDA activation count, etc.)
    ├── sizing/                 # Calculator JSON output (one file per size.py run)
    │   ├── execution-nodes.json
    │   ├── topology.json
    │   └── ocp-pods.yaml
    ├── <engagement>-quick-reference.md   # One-page output (topology first)
    └── <engagement>-sizing-report.md     # Full reasoning and calculator trace
```

## Planned examples

- `example/greenfield-enterprise-500hosts/` — containerized RHEL enterprise-b topology,
  500 managed hosts, 50 concurrent jobs, Automation Hub + EDA included
- `example/ocp-growth-200hosts/` — OCP Operator growth topology, 200 managed hosts,
  developer team use case

These will be added in v1 completion (see TODO.md).
