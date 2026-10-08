# Week 1 — baseline, 2026-10-08

Hardware: Intel i9-9880H, 32 GB, CPU only. Model: `qwen2.5:1.5b-instruct` (Q4_K_M via
Ollama). Prompt ≈ 25 tokens, `max_tokens` 150, streamed. Harness: `bench/load.py`.

| Runtime | Concurrency | Requests | Wall | TTFT p50 | TTFT p95 | Aggregate tok/s |
|---|---|---|---|---|---|---|
| Ollama (defaults) | 1 | 4 | 71.2 s | 0.26 s | 5.64 s | 8.4 |
| Ollama (defaults) | 4 | 8 | 155.9 s | 57.59 s | 59.47 s | 7.7 |

**Finding 1 — concurrency without parallel slots is a queue, not throughput.** Four
concurrent clients raised TTFT p50 by ~220× and *lowered* aggregate tokens/s. Ollama's default
serves one sequence at a time per loaded model; the other three requests wait their turn, so
the latency SLO is destroyed while the CPU is no busier. In Kafka terms: four consumers, one
partition.

**Next (week 2):** (a) `OLLAMA_NUM_PARALLEL=4` and re-run; expect TTFT to fall and per-request
tokens/s to drop as the CPU is shared — measure the trade-off; (b) the same test against
vLLM's CPU build, which does continuous batching; (c) record the KV-cache arithmetic for this
model so the parallel-slot limit is derived, not guessed.

The c=1 p95 of 5.64 s is a cold-start outlier (first request after model load); report both
cold and warm from now on.
