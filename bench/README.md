# Week 1–2 — serving + measurement (CPU only)

Goal: serve one small instruct model three ways and report, per runtime and concurrency:
TTFT p50/p95, inter-token latency, output tokens/s, RAM, and the KV-cache arithmetic.

Runtimes:
1. **llama.cpp** `llama-server` (GGUF Q4_K_M) — fastest on CPU, OpenAI-compatible.
2. **Ollama** — same engine, easier model management.
3. **vLLM CPU build** via Docker (x86, AVX2) — gives the *real* vLLM API surface and
   `/metrics` for Prometheus, which weeks 3–6 depend on.

Model: a 1–3B instruct model (e.g. Qwen2.5-1.5B-Instruct or Llama-3.2-3B-Instruct) — small
enough to run under 8 GB on CPU.

Load: `bench/load.py` (stdlib only) sends N concurrent chat completions with fixed prompt /
output lengths and records per-request timings; results to `results/*.csv`, summary to
`results/summary.md`.

KV-cache maths to document: bytes per token = 2 × n_layers × n_kv_heads × head_dim × dtype_bytes;
show it for the chosen model at fp16 and q8, and the max concurrent sequences that fit in a
given memory budget.
