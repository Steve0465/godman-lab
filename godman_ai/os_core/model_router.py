"""Model routing system for GodmanAI."""

import os
from typing import Optional, Dict, Any


class ModelRouter:
    """
    Routes tasks to appropriate AI models based on task type.
    
    Supports:
    - OpenAI models (gpt-4.1, gpt-4o, gpt-3.5-turbo)
    - Local models (llama.cpp, GGUF files)
    - Future: Gemini, Claude, etc.
    """

    def __init__(self, settings=None):
        self.settings = settings
        self._openai_client = None
        self._local_model = None
        
        # Model preferences by task type
        self.model_prefs = {
            "text_analysis": "gpt-3.5-turbo",
            "planning": "gpt-4o",
            "vision": "gpt-4o",
            "code_generation": "gpt-4o",
            "summarization": "gpt-3.5-turbo",
            "classification": "gpt-3.5-turbo",
            "default": "gpt-3.5-turbo",
        }
        
        # Override with settings if available
        if settings and hasattr(settings, "model_prefs"):
            self.model_prefs.update(settings.model_prefs)

    def choose_model(self, task_type: str) -> str:
        """
        Select the best model for a given task type.
        
        Args:
            task_type: Type of task (e.g., 'planning', 'vision', 'text_analysis')
            
        Returns:
            str: Model identifier to use
        """
        # Check if we have OpenAI key
        has_openai = bool(os.getenv("OPENAI_API_KEY"))
        
        model = self.model_prefs.get(task_type, self.model_prefs["default"])
        
        # Fallback to local if no OpenAI key
        if not has_openai:
            return "local-llama"
        
        return model

    def _get_openai_client(self):
        """Lazy load OpenAI client."""
        if self._openai_client is None:
            try:
                import openai
                self._openai_client = openai.OpenAI(
                    api_key=os.getenv("OPENAI_API_KEY")
                )
            except ImportError:
                raise RuntimeError("OpenAI package not installed. Run: pip install openai")
        return self._openai_client

    def _get_local_model(self):
        """Lazy load local model (placeholder for llama.cpp integration)."""
        if self._local_model is None:
            # TODO: Implement llama.cpp/GGUF model loading
            raise RuntimeError("Local model support not yet implemented")
        return self._local_model

    def run(
        self,
        prompt: str,
        model: Optional[str] = None,
        task_type: str = "default",
        **kwargs
    ) -> str:
        """
        Execute a prompt using the specified or automatically chosen model.
        
        Args:
            prompt: The prompt to send to the model
            model: Specific model to use (optional, will auto-select if None)
            task_type: Type of task for auto-selection
            **kwargs: Additional model parameters (temperature, max_tokens, etc.)
            
        Returns:
            str: Model response text
        """
        if model is None:
            model = self.choose_model(task_type)
        
        # Route to appropriate backend
        if model.startswith("gpt-"):
            return self._run_openai(prompt, model, **kwargs)
        elif model.startswith("local-"):
            return self._run_local(prompt, model, **kwargs)
        else:
            raise ValueError(f"Unknown model: {model}")

    def _run_openai(self, prompt: str, model: str, **kwargs) -> str:
        """
        Run prompt using OpenAI API.
        
        Args:
            prompt: The prompt text
            model: OpenAI model identifier
            **kwargs: OpenAI API parameters
            
        Returns:
            str: Model response
        """
        client = self._get_openai_client()
        
        # Default parameters
        params = {
            "temperature": 0.7,
            "max_tokens": 1000,
        }
        params.update(kwargs)
        
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                **params
            )
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {e}")

    def _run_local(self, prompt: str, model: str, **kwargs) -> str:
        """
        Run prompt using local Ollama model.
        
        Args:
            prompt: The prompt text
            model: Local model identifier
            **kwargs: Local model parameters
            
        Returns:
            str: Model response
        """
        try:
            import requests
        except ImportError:
            raise RuntimeError("requests package required. Run: pip install requests")
        
        # Get Ollama host from env or use default
        ollama_host = os.getenv("GODMAN_OLLAMA_HOST", "http://localhost:11434")
        model_name = os.getenv("GODMAN_LOCAL_MODEL_NAME", "llama3.2:3b")
        
        try:
            response = requests.post(
                f"{ollama_host}/api/generate",
                json={
                    "model": model_name,
                    "prompt": prompt,
                    "stream": False,
                    **kwargs
                },
                timeout=120
            )
            response.raise_for_status()
            return response.json()["response"]
        except Exception as e:
            raise RuntimeError(f"Ollama API error: {e}")

    def list_available_models(self) -> Dict[str, bool]:
        """
        List all models and their availability status.
        
        Returns:
            dict: Model names mapped to availability (True/False)
        """
        has_openai = bool(os.getenv("OPENAI_API_KEY"))
        
        # Check if Ollama is running
        has_ollama = self._check_ollama()
        
        return {
            "gpt-4o": has_openai,
            "gpt-4.1": has_openai,
            "gpt-3.5-turbo": has_openai,
            "local-llama": has_ollama,
        }
    
    def _check_ollama(self) -> bool:
        """Check if Ollama service is available."""
        try:
            import requests
            ollama_host = os.getenv("GODMAN_OLLAMA_HOST", "http://localhost:11434")
            response = requests.get(f"{ollama_host}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False
