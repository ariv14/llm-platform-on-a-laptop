"""Minimal OpenAI-compatible load generator (stdlib only).

Usage: python3 load.py --url http://localhost:8080/v1 --model <name> --concurrency 4 --requests 32
Records TTFT (first streamed token), total latency, output tokens; writes CSV to results/.
"""
from __future__ import annotations
import argparse, csv, json, os, threading, time, urllib.request
from datetime import datetime

PROMPT = "Explain, in about 150 words, how a Kafka consumer group rebalances partitions."

def one_request(url: str, model: str, max_tokens: int) -> dict:
    body = json.dumps({"model": model, "stream": True, "max_tokens": max_tokens,
                       "messages": [{"role": "user", "content": PROMPT}]}).encode()
    req = urllib.request.Request(f"{url}/chat/completions", data=body,
                                 headers={"Content-Type": "application/json"})
    t0 = time.perf_counter(); ttft = None; tokens = 0
    with urllib.request.urlopen(req, timeout=600) as resp:
        for line in resp:
            if not line.startswith(b"data:"): continue
            payload = line[5:].strip()
            if payload == b"[DONE]": break
            delta = json.loads(payload)["choices"][0].get("delta", {})
            if delta.get("content"):
                tokens += 1
                if ttft is None: ttft = time.perf_counter() - t0
    total = time.perf_counter() - t0
    return {"ttft_s": ttft, "total_s": total, "out_tokens": tokens,
            "tok_per_s": tokens / (total - (ttft or 0)) if total > (ttft or 0) else 0}

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8080/v1")
    ap.add_argument("--model", required=True)
    ap.add_argument("--concurrency", type=int, default=1)
    ap.add_argument("--requests", type=int, default=8)
    ap.add_argument("--max-tokens", type=int, default=200)
    ap.add_argument("--label", default="run")
    a = ap.parse_args()
    results: list[dict] = []; lock = threading.Lock(); remaining = [a.requests]
    def worker():
        while True:
            with lock:
                if remaining[0] <= 0: return
                remaining[0] -= 1
            r = one_request(a.url, a.model, a.max_tokens)
            with lock: results.append(r)
    threads = [threading.Thread(target=worker) for _ in range(a.concurrency)]
    t0 = time.perf_counter(); [t.start() for t in threads]; [t.join() for t in threads]
    wall = time.perf_counter() - t0
    os.makedirs("results", exist_ok=True)
    path = f"results/{a.label}-c{a.concurrency}-{datetime.now():%Y%m%d-%H%M%S}.csv"
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(results[0])); w.writeheader(); w.writerows(results)
    ttfts = sorted(r["ttft_s"] for r in results if r["ttft_s"] is not None)
    p = lambda q: ttfts[min(len(ttfts) - 1, int(q * len(ttfts)))]
    tot_tok = sum(r["out_tokens"] for r in results)
    print(f"{a.label} c={a.concurrency} n={len(results)} wall={wall:.1f}s "
          f"TTFT p50={p(0.5):.2f}s p95={p(0.95):.2f}s aggregate={tot_tok / wall:.1f} tok/s -> {path}")

if __name__ == "__main__":
    main()
