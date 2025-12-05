"""
Local model interface using Ollama.
Provides unrestricted LLM access for GodmanAI.
"""
import subprocess
import json
from typing import Optional


class LocalModel:
    """Interface to local Ollama models."""
    
    def __init__(self, model_name: str = "llama3.2:3b"):
        self.model_name = model_name
    
    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        """
        Generate text using local model.
        
        Args:
            prompt: User prompt
            system: Optional system message
            
        Returns:
            Generated text response
        """
        cmd = ["ollama", "run", self.model_name, prompt]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            return "Error: Model timeout"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def chat(self, messages: list[dict]) -> str:
        """
        Chat with model using conversation history.
        
        Args:
            messages: List of {role: str, content: str}
            
        Returns:
            Model response
        """
        # Convert to single prompt for simplicity
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            prompt_parts.append(f"{role.upper()}: {content}")
        
        full_prompt = "\n".join(prompt_parts)
        return self.generate(full_prompt)


def test_model():
    """Quick test of local model."""
    model = LocalModel()
    response = model.generate("Say hello in one sentence.")
    print(f"Model response: {response}")
    return response


if __name__ == "__main__":
    test_model()
