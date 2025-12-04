"""
Embeddings module for semantic search and clustering of extracted messages.

Uses sentence-transformers to compute embeddings and FAISS for efficient similarity search.

Example usage:
    from prototype.enhanced.embeddings import MessageEmbeddings
    
    embedder = MessageEmbeddings()
    embedder.add_messages([
        {'id': '1', 'text': 'Hello world'},
        {'id': '2', 'text': 'How are you?'}
    ])
    embedder.save('embeddings.pkl')
    
    # Search
    results = embedder.search('greeting', k=5)
"""

import numpy as np
import pickle
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import json

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

try:
    from sklearn.cluster import KMeans
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


@dataclass
class Message:
    """Represents a message with its metadata."""
    id: str
    text: str
    timestamp: Optional[str] = None
    sender: Optional[str] = None
    thread_id: Optional[str] = None
    metadata: Optional[Dict] = None
    
    def to_dict(self):
        return asdict(self)


class MessageEmbeddings:
    """
    Manage embeddings for messages with FAISS indexing for fast similarity search.
    """
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize the embeddings manager.
        
        Args:
            model_name: SentenceTransformer model name
        """
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError("sentence-transformers is required. Install with: pip install sentence-transformers")
        
        if not FAISS_AVAILABLE:
            raise ImportError("faiss-cpu is required. Install with: pip install faiss-cpu")
        
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        
        # Initialize FAISS index
        self.index = faiss.IndexFlatL2(self.dimension)
        
        # Store messages
        self.messages: List[Message] = []
        self.embeddings: Optional[np.ndarray] = None
    
    def add_messages(self, messages: List[Dict], batch_size: int = 32):
        """
        Add messages and compute their embeddings.
        
        Args:
            messages: List of message dictionaries
            batch_size: Batch size for embedding computation
        """
        if not messages:
            return
        
        # Convert to Message objects
        new_messages = []
        for msg in messages:
            if isinstance(msg, dict):
                new_messages.append(Message(**msg))
            elif isinstance(msg, Message):
                new_messages.append(msg)
            else:
                raise ValueError(f"Invalid message type: {type(msg)}")
        
        # Extract text for embedding
        texts = [msg.text for msg in new_messages]
        
        # Compute embeddings
        new_embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=len(texts) > 100,
            convert_to_numpy=True
        )
        
        # Add to index
        self.index.add(new_embeddings.astype('float32'))
        
        # Store messages and embeddings
        self.messages.extend(new_messages)
        
        if self.embeddings is None:
            self.embeddings = new_embeddings
        else:
            self.embeddings = np.vstack([self.embeddings, new_embeddings])
    
    def search(self, query: str, k: int = 5) -> List[Tuple[Message, float]]:
        """
        Search for similar messages.
        
        Args:
            query: Search query text
            k: Number of results to return
            
        Returns:
            List of (Message, distance) tuples
        """
        if len(self.messages) == 0:
            return []
        
        # Encode query
        query_embedding = self.model.encode([query], convert_to_numpy=True)
        
        # Search
        k = min(k, len(self.messages))
        distances, indices = self.index.search(query_embedding.astype('float32'), k)
        
        # Return results
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.messages):
                results.append((self.messages[idx], float(dist)))
        
        return results
    
    def cluster(self, n_clusters: int = 5) -> Dict[int, List[Message]]:
        """
        Cluster messages using K-means.
        
        Args:
            n_clusters: Number of clusters
            
        Returns:
            Dictionary mapping cluster ID to list of messages
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is required for clustering")
        
        if len(self.messages) < n_clusters:
            n_clusters = max(1, len(self.messages))
        
        if self.embeddings is None or len(self.embeddings) == 0:
            return {}
        
        # Perform clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(self.embeddings)
        
        # Group messages by cluster
        clusters = {}
        for i, label in enumerate(labels):
            label = int(label)
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(self.messages[i])
        
        return clusters
    
    def get_cluster_topics(self, n_clusters: int = 5, top_words: int = 5) -> Dict[int, List[str]]:
        """
        Get representative words for each cluster.
        
        Args:
            n_clusters: Number of clusters
            top_words: Number of top words per cluster
            
        Returns:
            Dictionary mapping cluster ID to list of representative words
        """
        clusters = self.cluster(n_clusters)
        
        topics = {}
        for cluster_id, messages in clusters.items():
            # Simple word frequency approach
            word_freq = {}
            for msg in messages:
                words = msg.text.lower().split()
                for word in words:
                    # Filter short words
                    if len(word) > 3:
                        word_freq[word] = word_freq.get(word, 0) + 1
            
            # Get top words
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            topics[cluster_id] = [word for word, _ in sorted_words[:top_words]]
        
        return topics
    
    def save(self, filepath: str):
        """
        Save embeddings and messages to file.
        
        Args:
            filepath: Output file path
        """
        data = {
            'messages': [msg.to_dict() for msg in self.messages],
            'embeddings': self.embeddings,
            'dimension': self.dimension
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(data, f)
        
        print(f"Saved {len(self.messages)} messages to {filepath}")
    
    @classmethod
    def load(cls, filepath: str, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Load embeddings and messages from file.
        
        Args:
            filepath: Input file path
            model_name: SentenceTransformer model name
            
        Returns:
            MessageEmbeddings instance
        """
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
        
        embedder = cls(model_name=model_name)
        
        # Restore messages
        embedder.messages = [Message(**msg) for msg in data['messages']]
        embedder.embeddings = data['embeddings']
        
        # Rebuild FAISS index
        if embedder.embeddings is not None and len(embedder.embeddings) > 0:
            embedder.index.add(embedder.embeddings.astype('float32'))
        
        print(f"Loaded {len(embedder.messages)} messages from {filepath}")
        
        return embedder
    
    def export_to_json(self, filepath: str):
        """Export messages and their metadata to JSON."""
        data = {
            'messages': [msg.to_dict() for msg in self.messages],
            'count': len(self.messages)
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)


def compute_message_sentiment(text: str) -> Dict[str, float]:
    """
    Simple sentiment analysis using word-based heuristics.
    
    This is a placeholder for more sophisticated sentiment analysis.
    
    Args:
        text: Message text
        
    Returns:
        Dictionary with sentiment scores
    """
    # Simple positive/negative word lists
    positive_words = {
        'good', 'great', 'excellent', 'happy', 'love', 'wonderful',
        'fantastic', 'amazing', 'best', 'awesome', 'nice', 'perfect',
        'yes', 'thank', 'thanks'
    }
    
    negative_words = {
        'bad', 'terrible', 'awful', 'hate', 'worst', 'horrible',
        'poor', 'sad', 'angry', 'upset', 'no', 'never', 'not'
    }
    
    words = text.lower().split()
    
    pos_count = sum(1 for w in words if w in positive_words)
    neg_count = sum(1 for w in words if w in negative_words)
    
    total = pos_count + neg_count
    
    if total == 0:
        return {'positive': 0.5, 'negative': 0.5, 'neutral': 1.0}
    
    positive_score = pos_count / total
    negative_score = neg_count / total
    neutral_score = 1.0 - max(positive_score, negative_score)
    
    return {
        'positive': positive_score,
        'negative': negative_score,
        'neutral': neutral_score
    }


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Message embeddings utilities')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Create embeddings
    create_parser = subparsers.add_parser('create', help='Create embeddings from messages JSON')
    create_parser.add_argument('input', help='Input JSON file with messages')
    create_parser.add_argument('output', help='Output pickle file')
    create_parser.add_argument('--model', default='all-MiniLM-L6-v2', help='Model name')
    
    # Search
    search_parser = subparsers.add_parser('search', help='Search for similar messages')
    search_parser.add_argument('embeddings', help='Embeddings pickle file')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument('--k', type=int, default=5, help='Number of results')
    
    # Cluster
    cluster_parser = subparsers.add_parser('cluster', help='Cluster messages')
    cluster_parser.add_argument('embeddings', help='Embeddings pickle file')
    cluster_parser.add_argument('--n', type=int, default=5, help='Number of clusters')
    cluster_parser.add_argument('--output', help='Output JSON file')
    
    args = parser.parse_args()
    
    if args.command == 'create':
        with open(args.input, 'r') as f:
            data = json.load(f)
        
        messages = data if isinstance(data, list) else data.get('messages', [])
        
        embedder = MessageEmbeddings(model_name=args.model)
        embedder.add_messages(messages)
        embedder.save(args.output)
    
    elif args.command == 'search':
        embedder = MessageEmbeddings.load(args.embeddings)
        results = embedder.search(args.query, k=args.k)
        
        print(f"\nTop {len(results)} results for '{args.query}':\n")
        for i, (msg, dist) in enumerate(results, 1):
            print(f"{i}. [distance={dist:.4f}] {msg.text[:100]}")
    
    elif args.command == 'cluster':
        embedder = MessageEmbeddings.load(args.embeddings)
        clusters = embedder.cluster(n_clusters=args.n)
        topics = embedder.get_cluster_topics(n_clusters=args.n)
        
        print(f"\nClustered into {len(clusters)} groups:\n")
        for cluster_id in sorted(clusters.keys()):
            messages = clusters[cluster_id]
            print(f"Cluster {cluster_id}: {len(messages)} messages")
            print(f"  Topics: {', '.join(topics.get(cluster_id, []))}")
            print(f"  Sample: {messages[0].text[:80]}...")
            print()
        
        if args.output:
            result = {
                'clusters': {
                    str(cid): [msg.to_dict() for msg in msgs]
                    for cid, msgs in clusters.items()
                },
                'topics': {str(k): v for k, v in topics.items()}
            }
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"Saved to {args.output}")
    
    else:
        parser.print_help()
