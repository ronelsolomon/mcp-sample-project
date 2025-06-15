import os
import time
import json
import threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import requests
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import sys
from pathlib import Path

# Add the current directory to the path so we can import tools
sys.path.append(str(Path(__file__).parent))

# Import the tool registry
from tools.registry import get_tool_registry
from tools.calculator import register_tools as register_calculator_tools

# Register tools
try:
    registry = get_tool_registry()
    register_calculator_tools(registry)
except Exception as e:
    print(f"Warning: Failed to register tools: {e}")

# Model state management
class ModelState(str, Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"

@dataclass
class ModelInfo:
    name: str
    state: ModelState = ModelState.STOPPED
    last_used: float = 0
    load_count: int = 0
    avg_response_time: float = 0
    error_count: int = 0

class ModelRequest(BaseModel):
    prompt: str
    max_tokens: int = 512
    temperature: float = 0.7

class ModelResponse(BaseModel):
    response: str
    model: str
    tokens_used: int
    processing_time: float

class MCP:
    def __init__(self):
        self.models: Dict[str, ModelInfo] = {}
        self.active_models: Dict[str, Any] = {}
        self.lock = threading.Lock()
        self.ollama_base_url = "http://localhost:11434"

    def add_model(self, model_name: str):
        """Add a new model to be managed by MCP"""
        with self.lock:
            if model_name not in self.models:
                self.models[model_name] = ModelInfo(name=model_name)
                return {"status": f"Model {model_name} added"}
            return {"status": f"Model {model_name} already exists"}

    def start_model(self, model_name: str):
        """Start a model if it's not already running"""
        if model_name not in self.models:
            return {"error": f"Model {model_name} not found"}
        
        with self.lock:
            model = self.models[model_name]
            if model.state == ModelState.RUNNING:
                return {"status": f"Model {model_name} is already running"}
            
            model.state = ModelState.STARTING
            
            try:
                # Check if model exists in Ollama, pull if not
                response = requests.get(f"{self.ollama_base_url}/api/tags")
                models = [m["name"] for m in response.json().get("models", [])]
                
                if model_name not in models:
                    print(f"Model {model_name} not found. Pulling...")
                    response = requests.post(
                        f"{self.ollama_base_url}/api/pull",
                        json={"name": model_name}
                    )
                    response.raise_for_status()
                
                model.state = ModelState.RUNNING
                model.last_used = time.time()
                return {"status": f"Model {model_name} started successfully"}
                
            except Exception as e:
                model.state = ModelState.ERROR
                model.error_count += 1
                return {"error": f"Failed to start model {model_name}: {str(e)}"}

    def stop_model(self, model_name: str):
        """Stop a running model"""
        with self.lock:
            if model_name in self.models:
                self.models[model_name].state = ModelState.STOPPED
                return {"status": f"Model {model_name} stopped"}
            return {"error": f"Model {model_name} not found"}

    def list_models(self):
        """List all managed models and their states"""
        with self.lock:
            return [asdict(model) for model in self.models.values()]

    def generate(self, model_name: str, request: ModelRequest) -> ModelResponse:
        """Generate a response using the specified model"""
        if model_name not in self.models:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model {model_name} not found"
            )
        
        model = self.models[model_name]
        if model.state != ModelState.RUNNING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Model {model_name} is not running"
            )
        
        start_time = time.time()
        try:
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json={
                    "model": model_name,
                    "prompt": request.prompt,
                    "options": {
                        "num_predict": request.max_tokens,
                        "temperature": request.temperature
                    }
                },
                timeout=60
            )
            response.raise_for_status()
            
            model.last_used = time.time()
            model.load_count += 1
            processing_time = time.time() - start_time
            
            # Update average response time
            if model.avg_response_time == 0:
                model.avg_response_time = processing_time
            else:
                model.avg_response_time = (model.avg_response_time + processing_time) / 2
            
            return ModelResponse(
                response=response.json().get("response", ""),
                model=model_name,
                tokens_used=response.json().get("eval_count", 0),
                processing_time=processing_time
            )
            
        except requests.exceptions.RequestException as e:
            model.error_count += 1
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Error generating response: {str(e)}"
            )

# Initialize FastAPI app
app = FastAPI(title="Model Control Protocol (MCP) Server")
mcp = MCP()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Endpoints
@app.post("/models/{model_name}/start")
async def start_model(model_name: str):
    return mcp.start_model(model_name)

@app.post("/models/{model_name}/stop")
async def stop_model(model_name: str):
    return mcp.stop_model(model_name)

@app.get("/models")
async def list_models():
    return mcp.list_models()

@app.post("/models/{model_name}/generate", response_model=ModelResponse)
async def generate_response(model_name: str, request: ModelRequest):
    return mcp.generate(model_name, request)

@app.get("/tools")
async def list_tools():
    """List all available tools"""
    registry = get_tool_registry()
    return {"tools": registry.list_tools()}

@app.post("/tools/execute")
async def execute_tool(tool_request: dict):
    """
    Execute a tool with the given parameters
    
    Request format:
    {
        "tool_name": "calculator",
        "parameters": {
            "expression": "2 + 2"
        }
    }
    """
    try:
        tool_name = tool_request.get("tool_name")
        parameters = tool_request.get("parameters", {})
        
        if not tool_name:
            raise HTTPException(status_code=400, detail="Missing tool_name")
            
        registry = get_tool_registry()
        result = registry.execute(tool_name, **parameters)
        
        return {
            "success": True,
            "result": result,
            "tool_name": tool_name
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Add some default models
    mcp.add_model("wizard-math:7b")
    mcp.add_model("llama2")
    
    # Start the server
    uvicorn.run(app, host="0.0.0.0", port=8000)
