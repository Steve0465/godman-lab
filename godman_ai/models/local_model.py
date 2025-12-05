"""
Local Model Integration for GodmanAI
Supports Ollama and other local model providers
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class LocalModelClient:
    """Client for interacting with local models via Ollama"""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self._available = None
    
    def is_available(self) -> bool:
        """Check if Ollama is running"""
        if self._available is not None:
            return self._available
            
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            self._available = response.status_code == 200
            return self._available
        except Exception:
            self._available = False
            return False
    
    def generate(
        self, 
        prompt: str, 
        model: str = "dolphin-llama3:8b",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """Generate completion using local model"""
        if not self.is_available():
            raise RuntimeError("Ollama not running. Start: brew services start ollama")
        
        import requests
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature}
        }
        
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        
        response = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=120)
        response.raise_for_status()
        return response.json().get("response", "")
    
    def list_models(self) -> list:
        """List available local models"""
        if not self.is_available():
            return []
        
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            return [m["name"] for m in response.json().get("models", [])]
        except Exception:
            return []


class HybridModelRouter:
    """Smart router between OpenAI and local models"""
    
    def __init__(self, prefer_local: bool = False, openai_key: Optional[str] = None):
        self.prefer_local = prefer_local
        self.openai_key = openai_key
        self.local_client = LocalModelClient()
    
    def route(self, task_type: str, prompt: str, **kwargs) -> str:
        """Route to best model based on task and availability"""
        
        # Vision requires OpenAI
        if task_type == "vision":
            return self._use_openai(prompt, **kwargs)
        
        # Prefer local if configured and available
        if self.prefer_local and self.local_client.is_available():
            return self._use_local(prompt, **kwargs)
        
        # Complex planning prefers OpenAI
        if task_type == "planning" and self.openai_key:
            return self._use_openai(prompt, **kwargs)
        
        # Try local, fallback to OpenAI
        if self.local_client.is_available():
            return self._use_local(prompt, **kwargs)
        elif self.openai_key:
            return self._use_openai(prompt, **kwargs)
        else:
            raise RuntimeError("No models available")
    
    def _use_local(self, prompt: str, **kwargs) -> str:
        logger.info("Using local model")
        return self.local_client.generate(prompt, **kwargs)
    
    def _use_openai(self, prompt: str, **kwargs) -> str:
        logger.info("Using OpenAI")
        import openai
        import os
        
        openai.api_key = self.openai_key or os.getenv("OPENAI_API_KEY")
        response = openai.chat.completions.create(
            model=kwargs.get("model", "gpt-4"),
            messages=[{"role": "user", "content": prompt}],
            temperature=kwargs.get("temperature", 0.7)
        )
        return response.choices[0].message.content
