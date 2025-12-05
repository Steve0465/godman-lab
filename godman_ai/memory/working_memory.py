"""
Working memory for short-lived context storage during task execution.
"""
from typing import Any, Dict, Optional


class WorkingMemory:
    """
    Short-lived in-memory storage for passing context between agent steps.
    Cleared after each task completion or manually.
    """
    
    def __init__(self):
        self._store: Dict[str, Any] = {}
    
    def push(self, key: str, value: Any):
        """
        Store a value in working memory.
        
        Args:
            key: Storage key
            value: Value to store
        """
        self._store[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a value from working memory.
        
        Args:
            key: Storage key
            default: Default value if key not found
            
        Returns:
            Stored value or default
        """
        return self._store.get(key, default)
    
    def pop(self, key: str, default: Any = None) -> Any:
        """
        Retrieve and remove a value from working memory.
        
        Args:
            key: Storage key
            default: Default value if key not found
            
        Returns:
            Stored value or default
        """
        return self._store.pop(key, default)
    
    def has(self, key: str) -> bool:
        """Check if key exists in working memory."""
        return key in self._store
    
    def keys(self):
        """Get all keys in working memory."""
        return self._store.keys()
    
    def clear(self):
        """Clear all working memory."""
        self._store.clear()
    
    def update(self, data: Dict[str, Any]):
        """
        Update working memory with multiple key-value pairs.
        
        Args:
            data: Dictionary of key-value pairs to store
        """
        self._store.update(data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Export working memory as dictionary."""
        return self._store.copy()
