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
        Run prompt using local model.
        
        Args:
            prompt: The prompt text
            model: Local model identifier
            **kwargs: Local model parameters
            
        Returns:
            str: Model response
        """
        # TODO: Implement local model support
        raise NotImplementedError("Local model support coming soon")

    def list_available_models(self) -> Dict[str, bool]:
        """
        List all models and their availability status.
        
        Returns:
            dict: Model names mapped to availability (True/False)
        """
        has_openai = bool(os.getenv("OPENAI_API_KEY"))
        
        return {
            "gpt-4o": has_openai,
            "gpt-4.1": has_openai,
            "gpt-3.5-turbo": has_openai,
            "local-llama": False,  # TODO: Check for local model files
        }
