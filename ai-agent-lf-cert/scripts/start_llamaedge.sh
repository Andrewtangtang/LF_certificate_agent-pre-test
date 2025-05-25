#!/bin/bash

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Path to the models and wasm files
LLAMA_DIR="$PROJECT_ROOT/../llama-api-server"
MODEL_PATH="$LLAMA_DIR/Llama-3.2-3B-Instruct-Q5_K_M.gguf"
EMBED_MODEL_PATH="$LLAMA_DIR/nomic-embed-text-v1.5-f16.gguf"
WASM_PATH="$LLAMA_DIR/llama-api-server.wasm"

# Check if the model files exist
if [ ! -f "$MODEL_PATH" ]; then
    echo "Error: Model file not found at $MODEL_PATH"
    exit 1
fi

if [ ! -f "$EMBED_MODEL_PATH" ]; then
    echo "Error: Embedding model file not found at $EMBED_MODEL_PATH"
    exit 1
fi

if [ ! -f "$WASM_PATH" ]; then
    echo "Error: WASM file not found at $WASM_PATH"
    exit 1
fi

echo "Starting LlamaEdge API server with models:"
echo "LLM: $MODEL_PATH"
echo "Embeddings: $EMBED_MODEL_PATH"

cd "$LLAMA_DIR"

wasmedge --dir .:. \
  --nn-preload default:GGML:AUTO:Llama-3.2-3B-Instruct-Q5_K_M.gguf \
  --nn-preload embedding:GGML:AUTO:nomic-embed-text-v1.5-f16.gguf \
  llama-api-server.wasm \
  --model-alias      default,embedding \
  --model-name       Llama-3.2-3B-Instruct-Q5_K_M,nomic-embed-text-v1.5-f16 \
  --prompt-template  llama-3-tool,embedding \
  --ctx-size         4096,4096 \
  --batch-size       128,8192 \
  --ubatch-size      128,8192 \
  --log-prompts --log-stat

