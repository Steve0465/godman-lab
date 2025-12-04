"""
Embeddings module for semantic analysis of extracted messages.

Uses sentence-transformers to compute embeddings and FAISS for efficient similarity search.

Example usage:
    from embeddings import MessageEmbedder
    
    embedder = MessageEmbedder()
    embedder.add_messages(['Hello', 'How are you?', 'Great!'])
    similar = embedder.search('greeting', k=2)
"""

import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
import json
import pickle

import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from sklearn.cluster import KMeans


class MessageEmbedder:
    """
    Manages embeddings for messages with semantic search and clustering.
    
    Uses sentence-transformers for embedding generation and FAISS for
    efficient similarity search.
    """
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2', index_path: Optional[str] = None):
        """
        Initialize the message embedder.
        
        Args:
            model_name: Name of the sentence-transformer model to use
            index_path: Path to load/save FAISS index and metadata
        """
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        
        self.index = faiss.IndexFlatL2(self.dimension)
        self.messages: List[str] = []
        self.metadata: List[Dict[str, Any]] = []
        
        self.index_path = index_path
        
        if index_path and os.path.exists(index_path):
            self.load(index_path)
    
    def add_message(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> int:
        """
        Add a single message to the index.
        
        Args:
            text: Message text
            metadata: Optional metadata associated with the message
            
        Returns:
            Index of the added message
        """
        return self.add_messages([text], [metadata] if metadata else None)[0]
    
    def add_messages(self, texts: List[str], 
                    metadata_list: Optional[List[Dict[str, Any]]] = None) -> List[int]:
        """
        Add multiple messages to the index.
        
        Args:
            texts: List of message texts
            metadata_list: Optional list of metadata dicts
            
        Returns:
            List of indices for the added messages
        """
        if not texts:
            return []
        
        # Generate embeddings
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        
        # Add to FAISS index
        self.index.add(embeddings.astype('float32'))
        
        # Store messages and metadata
        start_idx = len(self.messages)
        self.messages.extend(texts)
        
        if metadata_list:
            self.metadata.extend(metadata_list)
        else:
            self.metadata.extend([{}] * len(texts))
        
        return list(range(start_idx, start_idx + len(texts)))
    
    def search(self, query: str, k: int = 5) -> List[Tuple[int, str, float, Dict]]:
        """
        Search for similar messages.
        
        Args:
            query: Query text
            k: Number of results to return
            
        Returns:
            List of (index, message, distance, metadata) tuples
        """
        if self.index.ntotal == 0:
            return []
        
        # Generate query embedding
        query_embedding = self.model.encode([query], convert_to_numpy=True)
        
        # Search
        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(query_embedding.astype('float32'), k)
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx >= 0 and idx < len(self.messages):
                results.append((
                    int(idx),
                    self.messages[idx],
                    float(dist),
                    self.metadata[idx]
                ))
        
        return results
    
    def cluster_messages(self, n_clusters: int = 5) -> Dict[int, List[int]]:
        """
        Cluster messages using K-means.
        
        Args:
            n_clusters: Number of clusters
            
        Returns:
            Dictionary mapping cluster_id to list of message indices
        """
        if self.index.ntotal == 0:
            return {}
        
        # Get all embeddings from FAISS
        embeddings = np.zeros((self.index.ntotal, self.dimension), dtype='float32')
        for i in range(self.index.ntotal):
            embeddings[i] = self.index.reconstruct(i)
        
        # Cluster
        n_clusters = min(n_clusters, self.index.ntotal)
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(embeddings)
        
        # Group by cluster
        clusters = {}
        for idx, label in enumerate(labels):
            label = int(label)
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(idx)
        
        return clusters
    
    def get_cluster_representatives(self, clusters: Dict[int, List[int]], 
                                   n_per_cluster: int = 3) -> Dict[int, List[Tuple[int, str]]]:
        """
        Get representative messages from each cluster.
        
        Args:
            clusters: Cluster dictionary from cluster_messages()
            n_per_cluster: Number of representative messages per cluster
            
        Returns:
            Dictionary mapping cluster_id to list of (index, message) tuples
        """
        representatives = {}
        
        for cluster_id, message_indices in clusters.items():
            # Get cluster center
            embeddings = np.array([
                self.index.reconstruct(idx) 
                for idx in message_indices
            ])
            center = embeddings.mean(axis=0)
            
            # Find closest messages to center
            distances = np.linalg.norm(embeddings - center, axis=1)
            closest_indices = np.argsort(distances)[:n_per_cluster]
            
            representatives[cluster_id] = [
                (message_indices[i], self.messages[message_indices[i]])
                for i in closest_indices
            ]
        
        return representatives
    
    def get_message(self, index: int) -> Tuple[str, Dict[str, Any]]:
        """
        Get message and metadata by index.
        
        Args:
            index: Message index
            
        Returns:
            Tuple of (message, metadata)
        """
        if 0 <= index < len(self.messages):
            return self.messages[index], self.metadata[index]
        return "", {}
    
    def save(self, path: str) -> None:
        """
        Save index and metadata to disk.
        
        Args:
            path: Directory path to save to
        """
        save_path = Path(path)
        save_path.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, str(save_path / 'faiss.index'))
        
        # Save messages and metadata
        data = {
            'messages': self.messages,
            'metadata': self.metadata,
            'model_name': self.model_name,
            'dimension': self.dimension
        }
        
        with open(save_path / 'data.pkl', 'wb') as f:
            pickle.dump(data, f)
    
    def load(self, path: str) -> None:
        """
        Load index and metadata from disk.
        
        Args:
            path: Directory path to load from
        """
        load_path = Path(path)
        
        # Load FAISS index
        index_file = load_path / 'faiss.index'
        if index_file.exists():
            self.index = faiss.read_index(str(index_file))
        
        # Load messages and metadata
        data_file = load_path / 'data.pkl'
        if data_file.exists():
            with open(data_file, 'rb') as f:
                data = pickle.load(f)
            
            self.messages = data['messages']
            self.metadata = data['metadata']
            
            # Verify model compatibility
            if data['model_name'] != self.model_name:
                print(f"Warning: Loaded index uses {data['model_name']}, "
                      f"but current model is {self.model_name}")
    
    def export_to_json(self, output_path: str) -> None:
        """
        Export all messages and metadata to JSON.
        
        Args:
            output_path: Path to output JSON file
        """
        export_data = {
            'model': self.model_name,
            'num_messages': len(self.messages),
            'messages': [
                {
                    'index': i,
                    'text': msg,
                    'metadata': meta
                }
                for i, (msg, meta) in enumerate(zip(self.messages, self.metadata))
            ]
        }
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
    
    def compute_statistics(self) -> Dict[str, Any]:
        """
        Compute statistics about the indexed messages.
        
        Returns:
            Dictionary with statistics
        """
        if not self.messages:
            return {
                'num_messages': 0,
                'avg_length': 0,
                'total_words': 0
            }
        
        lengths = [len(msg) for msg in self.messages]
        word_counts = [len(msg.split()) for msg in self.messages]
        
        return {
            'num_messages': len(self.messages),
            'avg_length': sum(lengths) / len(lengths),
            'min_length': min(lengths),
            'max_length': max(lengths),
            'total_chars': sum(lengths),
            'avg_words': sum(word_counts) / len(word_counts),
            'total_words': sum(word_counts),
            'model': self.model_name,
            'embedding_dimension': self.dimension
        }


def compute_sentiment_scores(texts: List[str], model_name: str = 'all-MiniLM-L6-v2') -> List[float]:
    """
    Compute simple sentiment scores for texts.
    
    This is a simplified sentiment analysis based on cosine similarity
    with positive/negative reference embeddings.
    
    Args:
        texts: List of text messages
        model_name: Sentence transformer model name
        
    Returns:
        List of sentiment scores (-1 to 1, negative to positive)
    """
    if not texts:
        return []
    
    model = SentenceTransformer(model_name)
    
    # Reference texts for sentiment
    positive_ref = "I am very happy, excited, and joyful"
    negative_ref = "I am very sad, angry, and upset"
    
    # Get embeddings
    text_embeddings = model.encode(texts, convert_to_numpy=True)
    pos_embedding = model.encode([positive_ref], convert_to_numpy=True)[0]
    neg_embedding = model.encode([negative_ref], convert_to_numpy=True)[0]
    
    # Compute cosine similarities
    def cosine_similarity(a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    scores = []
    for embedding in text_embeddings:
        pos_sim = cosine_similarity(embedding, pos_embedding)
        neg_sim = cosine_similarity(embedding, neg_embedding)
        
        # Normalize to -1 to 1
        score = (pos_sim - neg_sim) / 2
        scores.append(float(score))
    
    return scores


def main():
    """CLI interface for message embeddings."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Manage message embeddings')
    parser.add_argument('--action', choices=['add', 'search', 'cluster', 'stats'],
                       required=True, help='Action to perform')
    parser.add_argument('--index', required=True, help='Path to FAISS index directory')
    parser.add_argument('--messages', help='JSON file with messages to add')
    parser.add_argument('--query', help='Query for search')
    parser.add_argument('--k', type=int, default=5, help='Number of results for search')
    parser.add_argument('--n-clusters', type=int, default=5, help='Number of clusters')
    parser.add_argument('--output', help='Output file for results')
    
    args = parser.parse_args()
    
    embedder = MessageEmbedder(index_path=args.index if os.path.exists(args.index) else None)
    
    if args.action == 'add':
        if not args.messages:
            print("Error: --messages required for add action")
            return
        
        with open(args.messages, 'r') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            texts = data
            metadata_list = None
        elif isinstance(data, dict) and 'messages' in data:
            texts = [m.get('text', '') for m in data['messages']]
            metadata_list = [m.get('metadata', {}) for m in data['messages']]
        else:
            print("Error: Invalid messages format")
            return
        
        indices = embedder.add_messages(texts, metadata_list)
        print(f"Added {len(indices)} messages to index")
        
        embedder.save(args.index)
        print(f"Saved index to {args.index}")
    
    elif args.action == 'search':
        if not args.query:
            print("Error: --query required for search action")
            return
        
        results = embedder.search(args.query, k=args.k)
        
        print(f"\nTop {len(results)} results for: '{args.query}'")
        print("-" * 80)
        
        for idx, msg, dist, meta in results:
            print(f"\n[{idx}] Distance: {dist:.4f}")
            print(f"Message: {msg}")
            if meta:
                print(f"Metadata: {meta}")
    
    elif args.action == 'cluster':
        clusters = embedder.cluster_messages(n_clusters=args.n_clusters)
        representatives = embedder.get_cluster_representatives(clusters)
        
        print(f"\nFound {len(clusters)} clusters:")
        print("-" * 80)
        
        for cluster_id, reps in representatives.items():
            print(f"\nCluster {cluster_id} ({len(clusters[cluster_id])} messages):")
            for idx, msg in reps:
                print(f"  - [{idx}] {msg[:80]}...")
        
        if args.output:
            output_data = {
                'n_clusters': len(clusters),
                'clusters': {
                    str(k): [int(i) for i in v] 
                    for k, v in clusters.items()
                },
                'representatives': {
                    str(k): [[int(i), msg] for i, msg in v]
                    for k, v in representatives.items()
                }
            }
            
            with open(args.output, 'w') as f:
                json.dump(output_data, f, indent=2)
            
            print(f"\nResults saved to {args.output}")
    
    elif args.action == 'stats':
        stats = embedder.compute_statistics()
        
        print("\nIndex Statistics:")
        print("-" * 80)
        for key, value in stats.items():
            if isinstance(value, float):
                print(f"{key}: {value:.2f}")
            else:
                print(f"{key}: {value}")
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(stats, f, indent=2)


if __name__ == '__main__':
    main()
