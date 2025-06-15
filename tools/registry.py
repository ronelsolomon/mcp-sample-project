from typing import Dict, Any, Callable, Optional, Type, Union, List, get_type_hints
from dataclasses import dataclass, asdict
import inspect
import json

@dataclass
class Tool:
    """Represents a tool that can be executed by the MCP system"""
    name: str
    function: Callable
    description: str
    parameters: dict
    return_type: Type
    
    def execute(self, **kwargs) -> Any:
        """Execute the tool with the given arguments"""
        return self.function(**kwargs)
    
    def to_dict(self) -> dict:
        """Convert the tool to a serializable dictionary"""
        return {
            'name': self.name,
            'description': self.description,
            'parameters': self._serialize_parameters(),
            'return_type': self._get_type_name(self.return_type)
        }
    
    def _serialize_parameters(self) -> dict:
        """Convert parameters to a serializable format"""
        params = {}
        for param_name, param_info in self.parameters.items():
            param_type = param_info.get('type', str)
            params[param_name] = {
                'type': self._get_type_name(param_type),
                'description': param_info.get('description', ''),
                'required': param_info.get('required', True)
            }
            if 'default' in param_info:
                params[param_name]['default'] = param_info['default']
        return params
    
    @staticmethod
    def _get_type_name(type_obj) -> str:
        """Get a string representation of a type"""
        if type_obj is None:
            return 'None'
        if hasattr(type_obj, '__name__'):
            return type_obj.__name__
        if hasattr(type_obj, '_name') and type_obj._name:
            return type_obj._name
        return str(type_obj)

class ToolRegistry:
    """Registry for managing and executing tools"""
    
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
    
    def register(self, 
                name: str, 
                function: Callable, 
                description: str = "",
                parameters: Optional[dict] = None,
                return_type: Type = str) -> None:
        """
        Register a new tool
        
        Args:
            name: Unique name for the tool
            function: The function to execute when the tool is called
            description: Description of what the tool does
            parameters: Dictionary describing the parameters the tool accepts
            return_type: The type of value the tool returns
        """
        if name in self._tools:
            raise ValueError(f"Tool '{name}' is already registered")
            
        # If parameters not provided, try to infer from function signature
        if parameters is None:
            parameters = {}
            sig = inspect.signature(function)
            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue
                param_type = param.annotation if param.annotation != inspect.Parameter.empty else str
                parameters[param_name] = {
                    'type': param_type,
                    'description': f"Parameter {param_name}",
                    'required': param.default == inspect.Parameter.empty
                }
                if param.default != inspect.Parameter.empty:
                    parameters[param_name]['default'] = param.default
        
        self._tools[name] = Tool(
            name=name,
            function=function,
            description=description,
            parameters=parameters,
            return_type=return_type
        )
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name"""
        return self._tools.get(name)
    
    def list_tools(self) -> List[dict]:
        """List all registered tools with their metadata"""
        return [tool.to_dict() for tool in self._tools.values()]
    
    def execute(self, tool_name: str, **kwargs) -> Any:
        """
        Execute a tool with the given arguments
        
        Args:
            tool_name: Name of the tool to execute
            **kwargs: Arguments to pass to the tool
            
        Returns:
            The result of the tool execution
            
        Raises:
            ValueError: If the tool is not found
            Exception: Any exception raised by the tool
        """
        tool = self.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")
            
        result = tool.execute(**kwargs)
        try:
            json.dumps(result)
        except TypeError:
            raise ValueError(f"Tool '{tool_name}' returned non-serializable result")
        return result

# Create a default registry
registry = ToolRegistry()

def get_tool_registry() -> ToolRegistry:
    """Get the default tool registry"""
    return registry
