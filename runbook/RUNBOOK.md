# Runbook — LLM inference platform

Format per entry: **Symptom → Detection (metric/alert) → Likely causes → Remediation → Verify
→ Prevent.** Written for the 03:00 on-call engineer, not for the author.

## Index

1. Queue depth climbing, TTFT breaching SLO
2. KV-cache exhaustion / request pre-emption (`vllm:kv_cache_usage_perc` ≈ 100)
3. GPU node NotReady — XID / ECC errors (DCGM)
4. NCCL hang on multi-GPU model start
5. Noisy neighbour: one tenant starves others (ResourceQuota / priority)
6. Driver / CUDA / container-toolkit upgrade with drain and canary
7. Gateway budget exhausted for a tenant (LiteLLM)
8. Model rollout rollback (new checkpoint, worse latency)

## 1. Queue depth climbing, TTFT breaching SLO

- **Symptom:** p95 `time_to_first_token_seconds` far above SLO while tokens/s is flat or
  falling. Reproduced 2026-10-08: TTFT p50 0.26 s → 57.6 s at four concurrent clients with
  one serving slot; throughput unchanged (see `bench/results/summary.md`).
- **Detection:** `LLMQueueDepthHigh` — `vllm:num_requests_waiting` > N for 5 m (vLLM) or
  gateway in-flight − server slots > 0 (Ollama/llama.cpp); `LLMTTFTp95High`.
- **Likely causes, in order:** (1) requests exceed serving slots / `max_num_seqs` — queueing,
  not saturation; (2) a replica unhealthy and out of the service, halving slots; (3) KV-cache
  full, sequences pre-empted (§2); (4) genuine CPU/GPU saturation (tokens/s at ceiling).
- **Remediation:** (1) check slots vs in-flight — if in-flight > slots and compute is idle,
  raise slots (`OLLAMA_NUM_PARALLEL`, vLLM `max_num_seqs`) *within the KV budget*; (2) scale
  replicas if HPA/KEDA has headroom; (3) shed load at the gateway (per-tenant rate limit)
  rather than let the queue grow; (4) if saturated, nothing but capacity or a smaller model.
- **Verify:** queue depth under threshold and TTFT p95 in SLO for 10 m; tokens/s not below
  the pre-incident baseline by more than the known slot overhead (−26 % measured for 4 slots).
- **Prevent:** size slots from arrival rate × SLO, not from "max the machine"; KEDA on queue
  depth; load test every model or runtime change at c = 1, 4, 16 before rollout.
- **Trade-off to state in the post-mortem:** slots cost throughput and reserve KV even when
  idle (single-client run slowed 8.4 → 5.5 tok/s with four slots). Latency SLO vs capacity is a
  decision for the service owner, not the on-call engineer.

## 2. KV-cache exhaustion / pre-emption

- **Symptom:** throughput collapses under long prompts; vLLM logs pre-emption/recompute;
  `vllm:kv_cache_usage_perc` ≈ 100.
- **Arithmetic first:** KV bytes/token = 2 × layers × kv_heads × head_dim × dtype_bytes.
  Qwen2.5-1.5B f16 = 28 KiB/token; Llama-3-8B f16 = 128 KiB/token. Max resident tokens =
  KV budget ÷ bytes/token; max concurrent sequences = that ÷ (prompt + output length).
- **Remediation:** cap `max_model_len` per tenant at the gateway; switch KV to q8/fp8 if
  quality allows; reduce slots; add replicas.
- **Verify / Prevent:** record the arithmetic in the service's capacity sheet; alert at 85 %.

_(§3–§8: to be written as each failure is reproduced in the lab; do not write from memory.)_
