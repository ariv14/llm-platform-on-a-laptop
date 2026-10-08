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

- **Symptom:** p95 `time_to_first_token_seconds` > SLO; `vllm:num_requests_waiting` rising.
- **Detection:** alert `LLMQueueDepthHigh` (for 5m) and `LLMTTFTp95High`.
- **Likely causes:** burst above capacity; `max_num_seqs` too low; long prompts filling
  KV-cache; a replica unhealthy and removed from the service.
- **Remediation:** (1) confirm replica count vs HPA/KEDA target; (2) scale out if GPU/CPU
  headroom exists; (3) if KV-bound, see §2; (4) if one replica, drain and restart it.
- **Verify:** queue depth returns under threshold within N minutes; TTFT p95 back in SLO.
- **Prevent:** KEDA on queue depth; per-tenant rate limits at the gateway; load test before
  each model change.

_(§2–§8: to be written as each failure is reproduced in the lab; do not write from memory.)_
