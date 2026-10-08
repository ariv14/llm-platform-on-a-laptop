MODEL ?= qwen2.5:1.5b-instruct
.PHONY: ollama-serve ollama-bench vllm-cpu kind-up kind-down

ollama-serve:            ## pull + run the week-1 model with Ollama (OpenAI-compatible on :11434)
	ollama pull $(MODEL)
	@echo "Ollama serves at http://localhost:11434/v1 — model $(MODEL)"

ollama-bench:            ## baseline load test against Ollama
	cd bench && python3 load.py --url http://localhost:11434/v1 --model $(MODEL) --concurrency 1 --requests 8 --label ollama
	cd bench && python3 load.py --url http://localhost:11434/v1 --model $(MODEL) --concurrency 4 --requests 16 --label ollama

vllm-cpu:                ## vLLM x86 CPU image (build once; see docs.vllm.ai "CPU" install page for the current tag/flags)
	@echo "docker run --rm -p 8000:8000 -e VLLM_CPU_KVCACHE_SPACE=8 <vllm-cpu-image> --model Qwen/Qwen2.5-1.5B-Instruct --dtype bfloat16"

kind-up:                 ## week 3: local cluster for fake-GPU scheduling work
	kind create cluster --name llm-lab --config k8s/kind.yaml

kind-down:
	kind delete cluster --name llm-lab
