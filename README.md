# Model Control Protocol (MCP) Implementation

A robust implementation of a Model Control Protocol server and client for managing and interacting with AI models using Ollama.

## Features

- Manage multiple AI models (start/stop)
- Monitor model resources and performance
- Load balancing between models
- Thread-safe operations
- Model state management
- Performance metrics collection
- Interactive CLI client
- RESTful API server

## Prerequisites

- Python 3.8+
- [Ollama](https://ollama.ai/) installed and running
- `ollama serve` should be running in a separate terminal

## Installation

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Quick Start

1. Start the MCP server in one terminal:
   ```bash
   python mcp_server.py
   ```

2. In another terminal, use the interactive client:
   ```bash
   python mcp_client.py
   ```

3. Or interact with the API directly:
   ```bash
   # List models
   curl http://localhost:8000/models
   
   # Start a model
   curl -X POST http://localhost:8000/models/wizard-math:7b/start
   
   # Generate a response
   curl -X POST http://localhost:8000/models/wizard-math:7b/generate \
     -H "Content-Type: application/json" \
     -d '{"prompt": "What is 5 times 5?", "max_tokens": 100}'
   ```

## API Endpoints

### List Models
`GET /models`

List all available models and their status.

### Start Model
`POST /models/{model_name}/start`

Start a specific model.

### Stop Model
`POST /models/{model_name}/stop`

Stop a specific model.

### Generate Response
`POST /models/{model_name}/generate`

Generate a response using the specified model.

**Request Body:**
```json
{
  "prompt": "Your prompt here",
  "max_tokens": 512,
  "temperature": 0.7
}
```

## Interactive Client Usage

The interactive client provides a user-friendly way to interact with the MCP server:

1. **List Models**: View all available models and their status
2. **Start Model**: Start a specific model
3. **Stop Model**: Stop a specific model
4. **Generate Response**: Get a response from a model
5. **Exit**: Close the client

## Configuration

Environment variables can be set in a `.env` file:

```
# MCP Server Configuration
HOST=0.0.0.0
PORT=8000

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
```

## License

MIT
