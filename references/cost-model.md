# Cost Model

Indicative cost guidance for AAP infrastructure. All prices are planning defaults — label them
"indicative, <date>" in every output. Never invent subscription prices; always defer to Red Hat.

---

## AAP Subscription

**Do not quote subscription prices.** Red Hat AAP subscription pricing depends on:
- Managed host count (socket pairs or managed nodes, depending on tier)
- Subscription tier (Standard, Premium)
- Multi-year discounts
- Partner / CCSP pricing

Always state: *"Contact your Red Hat account team or see [redhat.com/pricing](https://www.redhat.com/en/technologies/management/ansible/pricing) for current subscription pricing."*

The cost output from `size.py cost` includes **infrastructure only** — no subscription line.

---

## On-Premises Infrastructure (Indicative)

Source: A: UNVERIFIED planning defaults; use customer quote when available.

| Server class | vCPU | RAM | Use for | A: $/month (3-yr amortised) |
|---|---|---|---|---|
| Small VM | 4 vCPU | 16 GB | growth-a all-in-one, hop nodes | A: $100–200 |
| Medium VM | 8 vCPU | 32 GB | execution nodes, growth-b | A: $200–400 |
| Large VM | 16 vCPU | 64 GB | enterprise controller, Hub | A: $400–800 |
| XL VM | 32 vCPU | 128 GB | large-scale execution, HA Hub | A: $800–1,500 |

> These are commodity server + power + colo estimates. Use the customer's actual hardware quote.
> Amortise over 3 or 5 years as agreed with the customer.

---

## Cloud Infrastructure (Indicative)

Source: A: indicative cloud list prices; retrieved 2026. Always check current pricing.

### AWS (EC2 on-demand — us-east-1)

| Instance | vCPU | RAM | A: $/hr on-demand | A: $/hr 3-yr reserved |
|---|---|---|---|---|
| m6i.xlarge | 4 | 16 GB | ~$0.192 | ~$0.096 |
| m6i.2xlarge | 8 | 32 GB | ~$0.384 | ~$0.192 |
| m6i.4xlarge | 16 | 64 GB | ~$0.768 | ~$0.384 |
| m6i.8xlarge | 32 | 128 GB | ~$1.536 | ~$0.768 |

### Azure (on-demand — East US)

| Instance | vCPU | RAM | A: $/hr on-demand |
|---|---|---|---|
| Standard_D4s_v5 | 4 | 16 GB | ~$0.192 |
| Standard_D8s_v5 | 8 | 32 GB | ~$0.384 |
| Standard_D16s_v5 | 16 | 64 GB | ~$0.768 |

### GCP (on-demand — us-central1)

| Machine type | vCPU | RAM | A: $/hr on-demand |
|---|---|---|---|
| n2-standard-4 | 4 | 16 GB | ~$0.190 |
| n2-standard-8 | 8 | 32 GB | ~$0.380 |
| n2-standard-16 | 16 | 64 GB | ~$0.760 |

---

## OCP Worker Node Cost

For OCP Operator deployments, cost the **worker nodes** that host AAP pods, not the pods directly.

- AAP Gateway + Controller + EDA on OCP: A: 3 worker nodes minimum (4 vCPU / 16 GB each)
- Hub (Pulp): A: additional 2 worker nodes for storage-intensive workloads
- Add OCP subscription / ROSA / ARO cost separately — never invent it

---

## Monthly Cost Summary Template

```
Infrastructure cost (indicative, <date>):
  <N> × <instance/VM type> @ A: $<X>/month = $<total>/month
  Storage: <GB> @ A: $<rate>/GB/month = $<total>/month
  Network egress: A: negligible for internal-only AAP mesh
  Total infrastructure: A: ~$<total>/month

AAP subscription: contact Red Hat — see redhat.com/pricing
OpenShift subscription (if OCP): contact Red Hat

Note: All infrastructure prices are planning estimates. Use actual quotes before budgeting.
```

---

## Crossover: On-Prem vs Cloud

A: Break-even typically at 2–3 years for a stable, well-utilised deployment:
- Cloud favours: variable workloads, short-lived environments, no upfront capex
- On-prem favours: steady-state 24/7 workloads, existing data centre capacity, security/air-gap requirements

Always ask the customer their capex/opex preference before modelling cost.
