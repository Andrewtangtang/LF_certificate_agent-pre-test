#!/bin/bash

wasmedge --dir .:. \
  --nn-preload default:GGML:AUTO:Llama-3.2-8B-Instruct-Q4_K_M.gguf \
  --nn-preload embedding:GGML:AUTO:nomic-embed-text-v1.5-f16.gguf \
  llama-api-server.wasm \
  --model-alias default,embedding \
  --model-name Llama-3.2-8B-Instruct-Q4_K_M,nomic-embed-text-v1.5-f16 \
  --prompt-template llama-3-tool,embedding \
  --batch-size 128,8192 \
  --threads 8 \
  --ubatch-size 128,8192 \
  --ctx-size 4096,4096 \
  --log-prompts --log-stat
