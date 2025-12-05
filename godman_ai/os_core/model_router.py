"""
Model Router - intelligently routes tasks to local or cloud models
"""
import logging
from typing import Optional
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)

class ModelRouter:
    """Routes AI tasks to appropriate models (local or cloud)"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config = self._load_config(config_path)
        self.ollama_client = None
        self.openai_client = None
        
    def _load_config(self, config_path: Optional[Path] = None) -> dict:
        """Load model configuration"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "local_model_config.yaml"
        
        if config_path.exists():
            with open(config_path) as f:
                return yaml.safe_load(f)
        return {}
    
    def choose_model(self, task_type: str = "general") -> str:
        """Choose appropriate model based on task type"""
        routing = self.config.get("model_preferences", {}).get("task_routing", {})
        return routing.get(task_type, "dolphin-mixtral:8x7b")
    
    def run(self, prompt: str, model: Optional[str] = None, task_type: str = "general") -> str:
        """Execute prompt using appropriate model"""
        if model is None:
            model = self.choose_model(task_type)
        
        provider = self.config.get("model_preferences", {}).get("default_provider", "ollama")
        
        try:
            if provider == "ollama":
                return self._run_ollama(prompt, model)
            elif provider == "openai":
                return self._run_openai(prompt, model)
        except Exception as e:
            logger.error(f"Primary provider failed: {e}")
            # Try fallback
            return self._run_fallback(prompt, model)
    
    def _run_ollama(self, prompt: str, model: str) -> str:
        """Run prompt through Ollama"""
        if self.ollama_client is None:
            import ollama
            self.ollama_client = ollama
        
        response = self.ollama_client.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response["message"]["content"]
    
    def _run_openai(self, prompt: str, model: str) -> str:
        """Run prompt through OpenAI"""
        if self.openai_client is None:
            from openai import OpenAI
            import os
            self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        response = self.openai_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    
    def _run_fallback(self, prompt: str, model: str) -> str:
        """Try fallback providers"""
        fallback_order = self.config.get("model_preferences", {}).get("fallback_order", ["ollama", "openai"])
        
        for provider in fallback_order:
            try:
                if provider == "ollama":
                    return self._run_ollama(prompt, model)
                elif provider == "openai":
                    return self._run_openai(prompt, "gpt-4")
            except Exception as e:
                logger.warning(f"Fallback {provider} failed: {e}")
                continue
        
        raise Exception("All model providers failed")
