"""
Vector store for semantic search and embeddings storage.
Uses FAISS for efficient similarity search with lazy imports.
"""
import os
import json
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional


class VectorStore:
    """
    Simple local vector store using FAISS for similarity search.
    Stores embeddings and metadata to disk.
    """
    
    def __init__(self, store_path: str = ".godman/state/vector_store"):
        self.store_path = Path(store_path)
        self.store_path.mkdir(parents=True, exist_ok=True)
        
        self.index_path = self.store_path / "index.faiss"
        self.metadata_path = self.store_path / "metadata.json"
        
        self.index = None
        self.metadata: List[Dict[str, Any]] = []
        self.dimension = 1536  # OpenAI embedding dimension
        
        self._load()
    
    def _load(self):
        """Load existing index and metadata from disk."""
        try:
            if self.index_path.exists():
                import faiss
                self.index = faiss.read_index(str(self.index_path))
            
            if self.metadata_path.exists():
                with open(self.metadata_path, 'r') as f:
                    self.metadata = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load vector store: {e}")
    
    def _save(self):
        """Save index and metadata to disk."""
        try:
            if self.index is not None:
                import faiss
                faiss.write_index(self.index, str(self.index_path))
            
            with open(self.metadata_path, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            print(f"Error saving vector store: {e}")
    
    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using OpenAI API (lazy import)."""
        try:
            import openai
            from godman_ai.config.loader import load_settings
            
            settings = load_settings()
            if not settings.openai_api_key:
                raise ValueError("OpenAI API key not configured")
            
            client = openai.OpenAI(api_key=settings.openai_api_key)
            response = client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error getting embedding: {e}")
            # Return zero vector as fallback
            return [0.0] * self.dimension
    
    def add(self, text: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Add text and metadata to the vector store.
        
        Args:
            text: Text to embed and store
            metadata: Optional metadata dict to associate with the text
        """
        try:
            import faiss
            import numpy as np
            
            # Get embedding
            embedding = self._get_embedding(text)
            embedding_array = np.array([embedding], dtype='float32')
            
            # Initialize index if needed
            if self.index is None:
                self.index = faiss.IndexFlatL2(self.dimension)
            
            # Add to index
            self.index.add(embedding_array)
            
            # Store metadata
            meta = metadata or {}
            meta['text'] = text
            meta['id'] = len(self.metadata)
            self.metadata.append(meta)
            
            self._save()
            
        except Exception as e:
            print(f"Error adding to vector store: {e}")
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar texts in the vector store.
        
        Args:
            query: Search query text
            top_k: Number of results to return
            
        Returns:
            List of metadata dicts with 'score' added
        """
        if self.index is None or len(self.metadata) == 0:
            return []
        
        try:
            import numpy as np
            
            # Get query embedding
            query_embedding = self._get_embedding(query)
            query_array = np.array([query_embedding], dtype='float32')
            
            # Search
            k = min(top_k, len(self.metadata))
            distances, indices = self.index.search(query_array, k)
            
            # Build results
            results = []
            for i, idx in enumerate(indices[0]):
                if idx < len(self.metadata):
                    result = self.metadata[idx].copy()
                    result['score'] = float(distances[0][i])
                    results.append(result)
            
            return results
            
        except Exception as e:
            print(f"Error searching vector store: {e}")
            return []
    
    def clear(self):
        """Clear all data from the vector store."""
        self.index = None
        self.metadata = []
        self._save()
