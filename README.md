# AI Agent for LF Certificate Prep

This project implements an MCP (Module Communication Protocol) based AI assistant that helps users prepare for Linux Foundation certification exams using local LLM models.

## Features

- Randomly selects practice exam questions from a question bank
- Searches for relevant exam questions and answers based on user input (using vector embedding semantic search)
- Provides a natural language interaction interface through LLM

## System Architecture

```
ai-agent-lf-cert/
├── data/                       # Pre-prepared exam questions and answers
│   └── cka_qa.json             
├── mcp_server/                 # FastMCP server; implements 2 tools
│   └── main.py                 
├── cli_demo/                   # CLI demo: user → LLM → MCP → LLM → user
│   ├── chat_cli.py             
│   ├── mcp_client.py           # helper to call MCP endpoints
│   └── tools_schema.py         # defines OpenAI-style function schema
├── scripts/                    # helper scripts
│   └── start_llamaedge.sh      # launch LlamaEdge API server
├── requirements.txt            # Python dependencies
├── Pipfile                     # Pipenv manifest
└── README.md                   # this document
llama-api-server/               # local LLM runtime + model files
├── llama-api-server.wasm       # WasmEdge runtime binary
├── Llama-3.2-3B-Instruct-Q5_K_M.gguf  
├── nomic-embed-text-v1.5-f16.gguf     
└── run-3b.sh                   # script to start the LLM API
```
## Prerequisites

- **WasmEdge Runtime**: Required to run the local LLM server
- **Python 3.12**: For the MCP server and CLI demo
- **At least 16GB RAM**: To run the 8B parameter model efficiently

### Installing WasmEdge

If you don't have WasmEdge installed, run:

```bash
curl -sSf https://raw.githubusercontent.com/WasmEdge/WasmEdge/master/utils/install.sh | bash
```
 If  you don't have LLM(Llama-3.2-8B-Instruct-Q4_K_M) file  installed, run:
```bash 
huggingface-cli download tensorblock/Llama-3.2-8B-Instruct-GGUF --include "Llama-3.2-8B-Instruct-Q4_K_M.gguf" --local-dir ./
```

## Installation and Execution

### 1. Install Python Dependencies

First, install the necessary Python packages:

```bash
cd ai-agent-lf-cert
pip install -r requirements.txt
```

### 2. Start the Local LLM API Server

In one terminal window, start the local LLM server:

```bash
cd llama-api-server
chmod +x run-3b.sh
./run-3b.sh
```

The local API server will provide both:
- **LLM conversation functionality** using Llama-3.2-3B-Instruct model
- **Text vector embedding functionality** using nomic-embed-text model for semantic search

The server will start on `http://localhost:8080` by default.

### 3. Start the MCP Server

In another terminal window, use `openmcp` to run the MCP server:

```bash
cd ai-agent-lf-cert
python mcp_server/main.py
```

### 4. Run the CLI Demo

In a third terminal window:

```bash
cd ai-agent-lf-cert
python cli_demo/chat_cli.py
```

## Usage

- After starting the CLI, you can interact with the system by inputting questions
- Enter "Give me a practice question" or similar requests to get a random question
- Enter specific questions (such as "What is a Kubernetes Pod?") to search for relevant answers
- Enter "quit" or "exit" to end the conversation

## Feature Details

### Local LLM Processing

This system runs entirely locally using WasmEdge and GGUF model files:

- **Main LLM**: Llama-3.2-3B-Instruct (Q5_K_M quantized) for natural language understanding and generation
- **Embedding Model**: Nomic Embed Text v1.5 for semantic search capabilities
- **Runtime**: WasmEdge WebAssembly runtime for efficient model execution

### Semantic Search

The system uses vector embeddings and cosine similarity to implement semantic search. Compared to simple string matching, this method better understands the semantics of user questions and finds the most relevant answers:

1. When the system starts, it generates vector embeddings for all predefined questions using the local embedding model
2. When a user asks a question, the system generates a vector embedding for the question locally
3. Using cosine similarity, it calculates the semantic similarity between the user's question and predefined questions
4. It returns the question and answer with the highest similarity



## Configuration

### Model Configuration

The local LLM server is configured with:
- **Context size**: 4096 tokens for both models
- **Batch size**: 128 for LLM, 8192 for embedding
- **Threads**: 12 (adjust based on your CPU cores)

You can modify these settings in `llama-api-server/run-3b.sh`.

### API Endpoints

The local server provides OpenAI-compatible endpoints:
- **Chat completions**: `POST /v1/chat/completions`
- **Embeddings**: `POST /v1/embeddings`

## Troubleshooting

### Common Issues

1. **WasmEdge not found**: Make sure WasmEdge is properly installed and in your PATH
2. **Out of memory**: The 3B model requires at least 4-6GB RAM. Close other applications if needed
3. **MCP server connection failed**: Ensure the MCP server is running and on the correct port
4. **Local LLM API not responding**: Check that the LLM server started successfully and is listening on port 8080

### Performance Tips

- **CPU cores**: Adjust the `--threads` parameter in `run-3b.sh` to match your CPU cores
- **Memory**: Ensure sufficient RAM is available before starting the LLM server
- **Model loading**: Initial model loading may take 30-60 seconds

### Logs and Debugging

- The LLM server runs with `--log-prompts --log-stat` for debugging
- Check terminal output for any error messages during startup
- MCP server logs will show in the terminal where it's running

## Model Information

- **Llama-3.2-3B-Instruct**: Meta's instruction-tuned model, quantized to Q5_K_M for efficiency
- **Nomic Embed Text v1.5**: High-quality text embedding model for semantic search
- **Total disk space**: Approximately 2.5GB for both models

This setup ensures complete privacy and offline functionality for your Linux Foundation certification preparation. 
