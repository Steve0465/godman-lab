"""Memory Store - Persistent storage for agent context and history."""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import pickle


class MemoryStore:
    """
    Persistent storage for agent memory, context, and conversation history.
    
    Features:
    - Store and retrieve conversation history
    - Maintain user preferences and context
    - Track automation history
    - Store learned patterns
    """
    
    def __init__(self, storage_dir: Path = None):
        """
        Initialize memory store.
        
        Args:
            storage_dir: Directory for storing memory files
        """
        self.storage_dir = storage_dir or Path(__file__).parent / "data"
        self.storage_dir.mkdir(exist_ok=True)
        
        # Memory files
        self.conversation_file = self.storage_dir / "conversations.json"
        self.context_file = self.storage_dir / "context.json"
        self.history_file = self.storage_dir / "automation_history.json"
        self.preferences_file = self.storage_dir / "preferences.json"
        
        # In-memory caches
        self._conversation_cache = []
        self._context_cache = {}
        self._preferences_cache = {}
        
        # Load existing data
        self._load()
    
    def _load(self):
        """Load all memory data from disk."""
        if self.conversation_file.exists():
            with open(self.conversation_file) as f:
                self._conversation_cache = json.load(f)
        
        if self.context_file.exists():
            with open(self.context_file) as f:
                self._context_cache = json.load(f)
        
        if self.preferences_file.exists():
            with open(self.preferences_file) as f:
                self._preferences_cache = json.load(f)
    
    def _save(self):
        """Save all memory data to disk."""
        with open(self.conversation_file, 'w') as f:
            json.dump(self._conversation_cache, f, indent=2)
        
        with open(self.context_file, 'w') as f:
            json.dump(self._context_cache, f, indent=2)
        
        with open(self.preferences_file, 'w') as f:
            json.dump(self._preferences_cache, f, indent=2)
    
    def add_conversation(self, role: str, content: str, metadata: Dict = None):
        """
        Add a conversation entry.
        
        Args:
            role: Role (user, assistant, system)
            content: Message content
            metadata: Optional metadata
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "role": role,
            "content": content,
            "metadata": metadata or {}
        }
        self._conversation_cache.append(entry)
        self._save()
    
    def get_conversation_history(self, limit: int = None) -> List[Dict]:
        """
        Get conversation history.
        
        Args:
            limit: Maximum number of entries to return (None = all)
        
        Returns:
            List of conversation entries
        """
        if limit:
            return self._conversation_cache[-limit:]
        return self._conversation_cache
    
    def set_context(self, key: str, value: Any):
        """
        Set a context value.
        
        Args:
            key: Context key
            value: Context value
        """
        self._context_cache[key] = {
            "value": value,
            "updated_at": datetime.now().isoformat()
        }
        self._save()
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """
        Get a context value.
        
        Args:
            key: Context key
            default: Default value if key not found
        
        Returns:
            Context value or default
        """
        if key in self._context_cache:
            return self._context_cache[key]["value"]
        return default
    
    def set_preference(self, key: str, value: Any):
        """
        Set a user preference.
        
        Args:
            key: Preference key
            value: Preference value
        """
        self._preferences_cache[key] = value
        self._save()
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """
        Get a user preference.
        
        Args:
            key: Preference key
            default: Default value if key not found
        
        Returns:
            Preference value or default
        """
        return self._preferences_cache.get(key, default)
    
    def log_automation(self, workflow: str, status: str, details: Dict = None):
        """
        Log an automation execution.
        
        Args:
            workflow: Workflow name
            status: Execution status
            details: Additional details
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "workflow": workflow,
            "status": status,
            "details": details or {}
        }
        
        # Append to history file
        history = []
        if self.history_file.exists():
            with open(self.history_file) as f:
                history = json.load(f)
        
        history.append(entry)
        
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=2)
    
    def get_automation_history(self, limit: int = 100) -> List[Dict]:
        """
        Get automation history.
        
        Args:
            limit: Maximum number of entries
        
        Returns:
            List of automation log entries
        """
        if not self.history_file.exists():
            return []
        
        with open(self.history_file) as f:
            history = json.load(f)
        
        return history[-limit:]
    
    def clear_conversation_history(self):
        """Clear all conversation history."""
        self._conversation_cache = []
        self._save()
    
    def clear_all(self):
        """Clear all memory data."""
        self._conversation_cache = []
        self._context_cache = {}
        self._preferences_cache = {}
        self._save()
        
        if self.history_file.exists():
            self.history_file.unlink()
