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
    
    def list_tools(self) -> list:
        """List all available tools"""
        try:
            response = requests.get(f"{self.base_url}/tools")
            response.raise_for_status()
            return response.json().get("tools", [])
        except requests.exceptions.RequestException as e:
            print(f"Error listing tools: {e}")
            return []
    
    def execute_tool(self, tool_name: str, **kwargs) -> dict:
        """
        Execute a tool with the given parameters
        
        Args:
            tool_name: Name of the tool to execute
            **kwargs: Parameters to pass to the tool
            
        Returns:
            The tool's response as a dictionary
        """
        try:
            response = requests.post(
                f"{self.base_url}/tools/execute",
                json={
                    "tool_name": tool_name,
                    "parameters": kwargs
                }
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error executing tool {tool_name}: {e}")
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
        print("5. List tools")
        print("6. Execute tool")
        print("7. Exit")
        
        choice = input("\nEnter your choice (1-7): ").strip()
        
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
            # List tools
            print("\nFetching available tools...")
            tools = client.list_tools()
            if tools:
                print("\nAvailable tools:")
                for tool in tools:
                    print(f"\n- {tool['name']}")
                    print(f"  Description: {tool['description']}")
                    print(f"  Returns: {tool['return_type']}")
                    if tool['parameters']:
                        print("  Parameters:")
                        for param_name, param_info in tool['parameters'].items():
                            required = "(required)" if param_info.get('required', False) else "(optional)"
                            param_type = param_info.get('type', 'any')
                            if hasattr(param_type, '__name__'):
                                param_type = param_type.__name__
                            desc = param_info.get('description', '')
                            print(f"    - {param_name}: {param_type} {required}")
                            if desc:
                                print(f"      {desc}")
            else:
                print("No tools found or error fetching tools.")
                
        elif choice == "6":
            # Execute tool
            tool_name = input("\nEnter tool name to execute: ").strip()
            if not tool_name:
                print("Tool name cannot be empty")
                continue
                
            # Get tool info to show required parameters
            tools = client.list_tools()
            tool = next((t for t in tools if t['name'] == tool_name), None)
            
            if not tool:
                print(f"Tool '{tool_name}' not found")
                continue
                
            print(f"\nExecuting tool: {tool_name}")
            print(f"Description: {tool['description']}")
            
            # Collect parameters
            parameters = {}
            for param_name, param_info in tool['parameters'].items():
                required = param_info.get('required', False)
                param_type = param_info.get('type', str)
                desc = param_info.get('description', '')
                
                while True:
                    try:
                        prompt = f"  {param_name} ({param_type.__name__ if hasattr(param_type, '__name__') else param_type})"
                        if desc:
                            prompt += f" - {desc}"
                        prompt += ": "
                        
                        value = input(prompt).strip()
                        
                        if not value and required:
                            print("  This parameter is required")
                            continue
                            
                        # Try to convert to the specified type
                        if value:
                            if param_type == int:
                                value = int(value)
                            elif param_type == float:
                                value = float(value)
                            elif param_type == bool:
                                value = value.lower() in ('true', 'yes', 'y', '1')
                                
                        parameters[param_name] = value
                        break
                        
                    except ValueError as e:
                        print(f"  Invalid input: {e}")
            
            print("\nExecuting...")
            result = client.execute_tool(tool_name, **parameters)
            
            if 'error' in result:
                print(f"\nError: {result['error']}")
            else:
                print("\n=== Tool Result ===\n")
                print(result.get('result', 'No result returned'))
                print("\n==================")
                
        elif choice == "7":
            print("\nExiting MCP client. Goodbye!")
            break
            
        else:
            print("\nInvalid choice. Please enter a number between 1-7.")

if __name__ == "__main__":
    try:
        interactive_client()
    except KeyboardInterrupt:
        print("\nExiting MCP client. Goodbye!")
