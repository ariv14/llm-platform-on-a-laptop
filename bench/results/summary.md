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

## Week 2 (same day) — parallel slots: `OLLAMA_NUM_PARALLEL=4`

Warm runs (one warm-up request discarded). Server log confirms `Parallel:4 … KvSize:16384`
(4 slots × 4096 context) vs the default single slot.

| Runtime | Concurrency | Requests | Wall | TTFT p50 | TTFT p95 | Aggregate tok/s |
|---|---|---|---|---|---|---|
| Ollama, `NUM_PARALLEL=1` (default) | 1 | 4 | 71.2 s | 0.26 s | 5.64 s* | 8.4 |
| Ollama, `NUM_PARALLEL=1` (default) | 4 | 8 | 155.9 s | 57.59 s | 59.47 s | 7.7 |
| Ollama, `NUM_PARALLEL=4` | 1 | 4 | 108.1 s | 0.44 s | 0.54 s | 5.5 |
| Ollama, `NUM_PARALLEL=4` | 4 | 8 | 212.1 s | 1.40 s | 17.90 s | 5.7 |

\* cold start included.

**Finding 2 — parallel slots buy latency with throughput, and the bill is paid even when
idle.** Four slots cut TTFT p50 under load from 57.6 s to 1.4 s (41×) — the queue is gone — but
aggregate tokens/s fell 26% (7.7 → 5.7) on an 8-core CPU, and the *single-client* run also
slowed (8.4 → 5.5) because the slots pre-allocate KV memory and split the batch budget whether
or not they are used. The p95 of 17.9 s at c=4 is the last request in each wave waiting for a
slot: with 8 requests over 4 slots there are two waves, and the second wave's first token
cannot arrive until a first-wave sequence finishes. This is a scheduler-sizing decision, not a
tuning knob: choose slots from the latency SLO and the arrival rate, then provision
throughput for it — the same capacity exercise as YARN container sizing.

**KV-cache arithmetic, Qwen2.5-1.5B-Instruct** (28 layers, 2 KV heads (GQA), head_dim 128):
bytes per token = 2 (K,V) × 28 × 2 × 128 × 2 B (f16) = **28,672 B ≈ 28 KiB/token**.
Ollama's `KvSize 16384` therefore reserves ≈ 448 MiB of KV at f16 for four 4,096-token slots;
q8 KV would halve it. For a 7B Llama-class model (32 layers, 8 KV heads, head_dim 128) the same
formula gives 128 KiB/token — 16× more per token — which is why slot count, context length and
KV dtype are the three numbers that decide how many tenants a GPU can hold.

**Next:** vLLM CPU build (continuous batching, no fixed slots) on the same test; then
`k8s/` with the slot count expressed as a per-tenant ResourceQuota.
