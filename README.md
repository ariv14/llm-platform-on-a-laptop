# llm-platform-on-a-laptop

Running an LLM inference platform the way an operator runs any other cluster: scheduling,
multi-tenancy, SLOs, capacity, cost, and a runbook — on a laptop with no GPU, for $0.

**Who:** Arivoli Murugan — 15 years operating Hadoop and Kafka clusters in banks and
insurers, now applying the same discipline to GPU and inference infrastructure.
**Why:** to show, with numbers, that the operator's job on a GPU fleet is the operator's job
on any fleet, plus a thin new layer (serving runtimes, GPU health, LLM SLOs).

## Status

| Week | Milestone | Status |
|---|---|---|
| 1–2 | Serve a 1–3B model locally (llama.cpp, Ollama, vLLM CPU); measure TTFT / ITL / tokens-per-s; KV-cache maths | ☐ |
| 3–4 | kind + fake-gpu-operator + KWOK: GPU requests/limits, taints, priority classes, per-tenant ResourceQuota; KEDA on queue depth | ☐ |
| 5–6 | kube-prometheus-stack, vLLM + fake-DCGM dashboards, SLOs, Alertmanager; **RUNBOOK.md** | ☐ |
| 7–8 | LiteLLM gateway: virtual keys, budgets, fallback to free hosted tiers; Langfuse tracing; **COST.md** | ☐ |
| 9–10 | Gateway API Inference Extension + llm-d-inference-sim; prefix-aware routing | ☐ |
| 11–12 | LFS158; NCA-AIIO syllabus as vocabulary (NCCL / IB / MIG / DCGM) | ☐ |
| 13–14 | MCP server exposing cluster ops (GPU allocation, queue depth, cost) | ☐ |
| 15–16 | One real-GPU validation run (HF ZeroGPU); two write-ups | ☐ |

## Hardware

Intel Core i9-9880H (8c/16t, AVX2), 32 GB RAM, no GPU, macOS. Everything here runs on CPU or
simulates GPUs; the one real-GPU run uses a structurally free tier.

## Layout

```
bench/          week 1–2: serving + load-test scripts, results as CSV/markdown
k8s/            week 3–4: kind config, fake-gpu-operator, KWOK nodes, tenant manifests, KEDA
observability/  week 5–6: kube-prometheus values, Grafana dashboards (JSON), alert rules
gateway/        week 7–8: LiteLLM config, Langfuse compose/helm, tenant keys and budgets
runbook/        RUNBOOK.md — failure modes, detection, remediation, verification
mcp-server/     week 13–14: Python MCP server for cluster operations
docs/           COST.md, design notes, write-ups
```

## Principles

- Every claim in this README has a number and a script that produced it.
- Baseline → change → trade-off, for every optimisation.
- The runbook is the product; the dashboards exist to make the runbook executable.
