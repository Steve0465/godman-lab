"""
Episodic memory stores task episodes (input, plan, results) for recall.
Integrates with VectorStore for semantic search.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from pathlib import Path


class EpisodicMemory:
    """
    Stores episodes of task execution for later recall.
    Each episode contains: task_input, plan, results, timestamp.
    """
    
    def __init__(self, store_path: str = ".godman/state/episodic"):
        self.store_path = Path(store_path)
        self.store_path.mkdir(parents=True, exist_ok=True)
        
        self.episodes_file = self.store_path / "episodes.jsonl"
        self.vector_store = None
    
    def _get_vector_store(self):
        """Lazy-load vector store."""
        if self.vector_store is None:
            from godman_ai.memory.vector_store import VectorStore
            self.vector_store = VectorStore()
        return self.vector_store
    
    def add_episode(
        self,
        task_input: Any,
        plan: List[Dict],
        results: Dict[str, Any],
        metadata: Optional[Dict] = None
    ):
        """
        Store a complete task episode.
        
        Args:
            task_input: Original task input
            plan: List of planned steps
            results: Execution results
            metadata: Optional additional metadata
        """
        episode = {
            "timestamp": datetime.utcnow().isoformat(),
            "task_input": str(task_input),
            "plan": plan,
            "results": results,
            "metadata": metadata or {}
        }
        
        # Append to JSONL file
        with open(self.episodes_file, 'a') as f:
            f.write(json.dumps(episode) + '\n')
        
        # Add to vector store for semantic search
        summary = self._create_episode_summary(episode)
        vector_store = self._get_vector_store()
        vector_store.add(
            summary,
            metadata={
                "type": "episode",
                "timestamp": episode["timestamp"],
                "task_input": episode["task_input"]
            }
        )
    
    def _create_episode_summary(self, episode: Dict) -> str:
        """Create a text summary of episode for vector search."""
        task = episode.get("task_input", "")
        results = episode.get("results", {})
        output = results.get("final_output", "")
        
        return f"Task: {task}\nResult: {output}"
    
    def recall(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Recall similar episodes based on semantic search.
        
        Args:
            query: Search query
            top_k: Number of episodes to return
            
        Returns:
            List of similar episodes
        """
        vector_store = self._get_vector_store()
        results = vector_store.search(query, top_k=top_k)
        
        # Load full episodes
        episodes = self._load_all_episodes()
        
        # Match results to episodes
        recalled = []
        for result in results:
            timestamp = result.get("timestamp")
            for episode in episodes:
                if episode.get("timestamp") == timestamp:
                    episode_copy = episode.copy()
                    episode_copy["similarity_score"] = result.get("score", 0.0)
                    recalled.append(episode_copy)
                    break
        
        return recalled
    
    def _load_all_episodes(self) -> List[Dict]:
        """Load all episodes from JSONL file."""
        if not self.episodes_file.exists():
            return []
        
        episodes = []
        with open(self.episodes_file, 'r') as f:
            for line in f:
                if line.strip():
                    episodes.append(json.loads(line))
        return episodes
    
    def get_recent(self, limit: int = 10) -> List[Dict]:
        """Get most recent episodes."""
        episodes = self._load_all_episodes()
        return episodes[-limit:]
    
    def clear(self):
        """Clear all episodic memory."""
        if self.episodes_file.exists():
            self.episodes_file.unlink()
