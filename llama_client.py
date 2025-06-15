import os
from typing import Optional
import ollama
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class WizardMathClient:
    def __init__(self, model_name: str = "wizard-math:7b"):
        """
        Initialize the WizardMath client with Ollama.
        
        Args:
            model_name: Name of the Ollama model to use (default: wizard-math:7b)
        """
        self.model_name = model_name
        self.client = ollama.Client()
        
        # Check if model is available, if not try to pull it
        try:
            self.client.show(self.model_name)
        except Exception:
            print(f"Model {self.model_name} not found. Attempting to pull...")
            self.client.pull(self.model_name)
    
    def generate_math_response(self, prompt: str, max_tokens: int = 512, temperature: float = 0.7) -> str:
        """
        Generate a response to a math-related question.
        
        Args:
            prompt: The math question or prompt
            max_tokens: Maximum number of tokens to generate
            temperature: Controls randomness (lower = more focused, higher = more creative)
            
        Returns:
            The model's response as a string
        """
        # Format the prompt for the wizard-math model
        formatted_prompt = f"""### Instruction:
{prompt}

### Response:
"""
        
        response = self.client.chat(
            model=self.model_name,
            messages=[
                {"role": "user", "content": formatted_prompt}
            ],
            options={
                'num_predict': max_tokens,
                'temperature': temperature,
                'stop': ["###"]
            }
        )
        
        return response['message']['content'].strip()

def main():
    # Example usage
    model_name = os.getenv("MODEL_NAME", "wizard-math:7b")
    
    try:
        print("Initializing Wizard Math Assistant with Ollama...")
        client = WizardMathClient(model_name=model_name)
        
        print("\nWizard Math Assistant initialized. Type 'quit' to exit.")
        print("Enter your math question:")
        
        while True:
            try:
                user_input = input("> ")
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                    
                if not user_input.strip():
                    continue
                    
                print("\nThinking...")
                response = client.generate_math_response(user_input)
                print("\nAssistant:", response)
                print("\n" + "="*50 + "\n")
                
            except KeyboardInterrupt:
                print("\nUse 'quit' to exit the program.")
                continue
            except Exception as e:
                print(f"\nError: {str(e)}")
                print("Make sure Ollama is running and the model is available.")
                continue
                
    except Exception as e:
        print(f"Error initializing the model: {str(e)}")
        print("Please ensure Ollama is installed and running.")
        print("You can install it with: brew install ollama")
        print("Then start it with: ollama serve")

if __name__ == "__main__":
    main()
