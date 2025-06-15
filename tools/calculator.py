import math
import re
import sys
from typing import Dict, Any, Union, Optional
from numbers import Number
from .registry import get_tool_registry

class CalculatorError(Exception):
    """Custom exception for calculator errors"""
    pass

def lcm(a: int, b: int) -> int:
    """Calculate the least common multiple of two integers"""
    return abs(a * b) // math.gcd(a, b) if a and b else 0

class Calculator:
    """
    A secure calculator that evaluates mathematical expressions.
    Supports basic arithmetic, trigonometric functions, and constants.
    """
    
    # Safe builtins for eval
    SAFE_GLOBALS = {
        # Constants
        'pi': math.pi,
        'e': math.e,
        'tau': math.tau,
        'inf': float('inf'),
        'nan': float('nan'),
        
        # Math functions
        'sqrt': math.sqrt,
        'pow': math.pow,
        'exp': math.exp,
        'log': math.log,
        'log10': math.log10,
        'log2': math.log2,
        'factorial': math.factorial,
        'gcd': math.gcd,
        'lcm': lcm,  # Using our custom lcm function
        'degrees': math.degrees,
        'radians': math.radians,
        
        # Trigonometric functions
        'sin': math.sin,
        'cos': math.cos,
        'tan': math.tan,
        'asin': math.asin,
        'acos': math.acos,
        'atan': math.atan,
        'atan2': math.atan2,
        'sinh': math.sinh,
        'cosh': math.cosh,
        'tanh': math.tanh,
        'asinh': math.asinh,
        'acosh': math.acosh,
        'atanh': math.atanh,
        
        # Other functions
        'abs': abs,
        'round': round,
        'min': min,
        'max': max,
        'sum': sum,
    }
    
    @classmethod
    def evaluate(cls, expression: str) -> float:
        """
        Safely evaluate a mathematical expression.
        
        Args:
            expression: The mathematical expression to evaluate
            
        Returns:
            The result of the evaluation as a float
            
        Raises:
            CalculatorError: If the expression is invalid or contains unsafe operations
        """
        if not expression or not isinstance(expression, str):
            raise CalculatorError("Expression must be a non-empty string")
        
        # Remove any whitespace
        expr = ''.join(expression.split())
        
        # Basic validation of the expression
        if not cls._is_valid_expression(expr):
            raise CalculatorError("Invalid mathematical expression")
        
        try:
            # Evaluate the expression in a safe environment
            result = eval(expr, {'__builtins__': {}}, cls.SAFE_GLOBALS)
            
            # Ensure the result is a number
            if not isinstance(result, Number):
                raise CalculatorError("Expression did not evaluate to a number")
                
            return float(result)
            
        except ZeroDivisionError:
            raise CalculatorError("Division by zero")
        except Exception as e:
            raise CalculatorError(f"Error evaluating expression: {str(e)}")
    
    @classmethod
    def _is_valid_expression(cls, expr: str) -> bool:
        """Check if the expression contains only allowed characters and patterns"""
        # Allowed characters: digits, basic operators, parentheses, decimal point, and function names
        allowed_pattern = r'^[\d\+\-*/%^(). \w]+$'
        if not re.match(allowed_pattern, expr):
            return False
            
        # Check for disallowed patterns
        disallowed_patterns = [
            r'__',  # No double underscores (could access private attributes)
            r'\b(?:exec|eval|open|file|import|os\.|subprocess\.|__[a-zA-Z0-9_]+__)\b',  # No dangerous functions
            r'[^\w]import\s+',  # No import statements
            r'[^\w]lambda\b',  # No lambda functions
            r'[^\w]print\b',  # No print statements
            r'[^\w]input\b',  # No input function
        ]
        
        for pattern in disallowed_patterns:
            if re.search(pattern, expr):
                return False
                
        return True

def calculate(expression: str) -> float:
    """
    Calculate the result of a mathematical expression.
    
    Args:
        expression: The mathematical expression to evaluate
        
    Returns:
        The result of the calculation
        
    Example:
        >>> calculate("2 + 2 * 2")
        6.0
        >>> calculate("sqrt(16) + abs(-5)")
        9.0
    """
    return Calculator.evaluate(expression)

def register_tools(registry=None):
    """
    Register calculator tools with the provided registry.
    
    Args:
        registry: The tool registry to register with. If None, uses the default registry.
    """
    if registry is None:
        registry = get_tool_registry()
    
    registry.register(
        name="calculator",
        function=calculate,
        description="Evaluate mathematical expressions. Supports basic arithmetic, trigonometric functions, and more.",
        parameters={
            "expression": {
                "type": str,
                "description": "The mathematical expression to evaluate (e.g., '2 + 2 * 2', 'sin(pi/2)')",
                "required": True
            }
        },
        return_type=float
    )

# Example usage
if __name__ == "__main__":
    # Register the calculator tool
    register_tools()
    
    # Get the registry and list available tools
    registry = get_tool_registry()
    print("Available tools:")
    for tool in registry.list_tools():
        print(f"- {tool['name']}: {tool['description']}")
    
    # Example usage
    test_expressions = [
        "2 + 2 * 2",
        "sin(pi/2)",
        "sqrt(16) + abs(-5)",
        "factorial(5)",
        "2 * (3 + 4)",
    ]
    
    print("\nTesting calculator:")
    for expr in test_expressions:
        try:
            result = registry.execute("calculator", expression=expr)
            print(f"{expr} = {result}")
        except Exception as e:
            print(f"Error evaluating '{expr}': {e}")