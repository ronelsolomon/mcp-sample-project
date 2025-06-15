import os
import time
import requests
from typing import Optional, Dict, Any
from enum import Enum

class MCPClient:
    """Client for interacting with the Model Control Protocol (MCP) server"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize the MCP client with the server URL"""
        self.base_url = base_url.rstrip('/')
    
    def list_models(self) -> Dict[str, Any]:
        """List all available models and their status"""
        try:
            response = requests.get(f"{self.base_url}/models")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error listing models: {e}")
            return {}
    
    def start_model(self, model_name: str) -> Dict[str, Any]:
        """Start a specific model"""
        try:
            response = requests.post(f"{self.base_url}/models/{model_name}/start")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error starting model {model_name}: {e}")
            return {"error": str(e)}
    
    def stop_model(self, model_name: str) -> Dict[str, Any]:
        """Stop a specific model"""
        try:
            response = requests.post(f"{self.base_url}/models/{model_name}/stop")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error stopping model {model_name}: {e}")
            return {"error": str(e)}
    
    def generate_response(
        self, 
        model_name: str, 
        prompt: str, 
        max_tokens: int = 512, 
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Generate a response from the specified model"""
        try:
            response = requests.post(
                f"{self.base_url}/models/{model_name}/generate",
                json={
                    "prompt": prompt,
                    "max_tokens": max_tokens,
                    "temperature": temperature
                },
                timeout=300  # 5 minute timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error generating response: {e}")
            return {"error": str(e)}

def interactive_client():
    """Interactive CLI for the MCP client"""
    client = MCPClient()
    
    print("\n=== Model Control Protocol (MCP) Client ===\n")
    
    while True:
        print("\nAvailable commands:")
        print("1. List models")
        print("2. Start model")
        print("3. Stop model")
        print("4. Generate response")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == "1":
            # List models
            print("\nFetching models...")
            models = client.list_models()
            if models:
                print("\nAvailable models:")
                for model in models:
                    print(f"\n- {model['name']} (Status: {model['state']})")
                    print(f"  Last used: {time.ctime(model['last_used'])}" if model['last_used'] > 0 else "  Never used")
                    print(f"  Load count: {model['load_count']}")
                    print(f"  Avg. response time: {model['avg_response_time']:.2f}s")
                    print(f"  Error count: {model['error_count']}")
            else:
                print("No models found or error fetching models.")
                
        elif choice == "2":
            # Start model
            model_name = input("\nEnter model name to start (e.g., wizard-math:7b): ").strip()
            if model_name:
                print(f"Starting {model_name}...")
                result = client.start_model(model_name)
                print(f"Result: {result}")
                
        elif choice == "3":
            # Stop model
            model_name = input("\nEnter model name to stop: ").strip()
            if model_name:
                print(f"Stopping {model_name}...")
                result = client.stop_model(model_name)
                print(f"Result: {result}")
                
        elif choice == "4":
            # Generate response
            model_name = input("\nEnter model name to use: ").strip()
            if not model_name:
                print("Model name cannot be empty")
                continue
                
            prompt = input("\nEnter your prompt (or 'back' to return):\n> ")
            if prompt.lower() == 'back':
                continue
                
            print("\nGenerating response...")
            start_time = time.time()
            response = client.generate_response(model_name, prompt)
            
            if 'error' in response:
                print(f"\nError: {response['error']}")
            else:
                print(f"\n=== Response (took {response.get('processing_time', 0):.2f}s) ===\n")
                print(response.get('response', 'No response received'))
                print("\n=== End of Response ===")
                
        elif choice == "5":
            print("\nExiting MCP client. Goodbye!")
            break
            
        else:
            print("\nInvalid choice. Please enter a number between 1-5.")

if __name__ == "__main__":
    try:
        interactive_client()
    except KeyboardInterrupt:
        print("\nExiting MCP client. Goodbye!")
