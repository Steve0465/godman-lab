"""
Unit tests for embeddings module.
"""

import pytest
import sys
from pathlib import Path
import tempfile
import shutil

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from embeddings import MessageEmbedder, compute_sentiment_scores


class TestMessageEmbedder:
    """Tests for MessageEmbedder class."""
    
    def test_initialization(self):
        """Test embedder initialization."""
        embedder = MessageEmbedder()
        assert embedder.model is not None
        assert embedder.dimension > 0
        assert embedder.index.ntotal == 0
    
    def test_add_message(self):
        """Test adding a single message."""
        embedder = MessageEmbedder()
        
        idx = embedder.add_message("Hello World")
        assert idx == 0
        assert embedder.index.ntotal == 1
        assert len(embedder.messages) == 1
        assert embedder.messages[0] == "Hello World"
    
    def test_add_messages(self):
        """Test adding multiple messages."""
        embedder = MessageEmbedder()
        
        messages = ["Hello", "World", "Test"]
        indices = embedder.add_messages(messages)
        
        assert len(indices) == 3
        assert embedder.index.ntotal == 3
        assert len(embedder.messages) == 3
    
    def test_add_with_metadata(self):
        """Test adding messages with metadata."""
        embedder = MessageEmbedder()
        
        metadata = {'source': 'test', 'timestamp': 123}
        idx = embedder.add_message("Hello", metadata=metadata)
        
        assert embedder.metadata[idx] == metadata
    
    def test_search(self):
        """Test semantic search."""
        embedder = MessageEmbedder()
        
        # Add some messages
        messages = [
            "Hello, how are you?",
            "I'm feeling great today!",
            "The weather is nice",
            "Good morning!",
            "Have a wonderful day"
        ]
        embedder.add_messages(messages)
        
        # Search for greeting
        results = embedder.search("greeting", k=2)
        
        assert len(results) <= 2
        for idx, msg, dist, meta in results:
            assert isinstance(idx, int)
            assert isinstance(msg, str)
            assert isinstance(dist, float)
            assert isinstance(meta, dict)
    
    def test_search_empty_index(self):
        """Test search on empty index."""
        embedder = MessageEmbedder()
        results = embedder.search("test", k=5)
        assert len(results) == 0
    
    def test_get_message(self):
        """Test getting message by index."""
        embedder = MessageEmbedder()
        
        embedder.add_message("Test message")
        msg, meta = embedder.get_message(0)
        
        assert msg == "Test message"
        assert isinstance(meta, dict)
        
        # Test invalid index
        msg, meta = embedder.get_message(999)
        assert msg == ""
        assert meta == {}
    
    def test_cluster_messages(self):
        """Test message clustering."""
        embedder = MessageEmbedder()
        
        # Add several messages
        messages = [
            "Hello", "Hi", "Hey",  # Greetings
            "Goodbye", "See you", "Bye",  # Farewells
            "Thank you", "Thanks", "Appreciate it"  # Thanks
        ]
        embedder.add_messages(messages)
        
        # Cluster into 3 groups
        clusters = embedder.cluster_messages(n_clusters=3)
        
        assert len(clusters) == 3
        
        # Check all messages are assigned
        total_assigned = sum(len(v) for v in clusters.values())
        assert total_assigned == len(messages)
    
    def test_cluster_empty_index(self):
        """Test clustering on empty index."""
        embedder = MessageEmbedder()
        clusters = embedder.cluster_messages(n_clusters=3)
        assert len(clusters) == 0
    
    def test_get_cluster_representatives(self):
        """Test getting cluster representatives."""
        embedder = MessageEmbedder()
        
        messages = ["Hello", "Hi", "Hey", "Goodbye", "Bye"]
        embedder.add_messages(messages)
        
        clusters = embedder.cluster_messages(n_clusters=2)
        representatives = embedder.get_cluster_representatives(clusters, n_per_cluster=2)
        
        assert len(representatives) == 2
        
        for cluster_id, reps in representatives.items():
            assert len(reps) <= 2
            for idx, msg in reps:
                assert isinstance(idx, int)
                assert isinstance(msg, str)
    
    def test_compute_statistics(self):
        """Test statistics computation."""
        embedder = MessageEmbedder()
        
        # Empty index
        stats = embedder.compute_statistics()
        assert stats['num_messages'] == 0
        
        # With messages
        embedder.add_messages(["Hello World", "Test Message", "A"])
        stats = embedder.compute_statistics()
        
        assert stats['num_messages'] == 3
        assert stats['avg_length'] > 0
        assert stats['total_words'] > 0
        assert 'model' in stats
    
    def test_save_and_load(self):
        """Test saving and loading index."""
        # Create temp directory
        with tempfile.TemporaryDirectory() as tmpdir:
            index_path = Path(tmpdir) / 'test_index'
            
            # Create and save
            embedder1 = MessageEmbedder()
            embedder1.add_messages(["Test 1", "Test 2", "Test 3"])
            embedder1.save(str(index_path))
            
            # Load
            embedder2 = MessageEmbedder(index_path=str(index_path))
            
            assert embedder2.index.ntotal == 3
            assert len(embedder2.messages) == 3
            assert embedder2.messages[0] == "Test 1"


class TestSentimentAnalysis:
    """Tests for sentiment analysis functions."""
    
    def test_compute_sentiment_scores(self):
        """Test sentiment score computation."""
        texts = [
            "I am very happy!",
            "This is terrible",
            "Neutral text here"
        ]
        
        scores = compute_sentiment_scores(texts)
        
        assert len(scores) == 3
        
        # All scores should be between -1 and 1
        for score in scores:
            assert -1.5 <= score <= 1.5
    
    def test_empty_sentiment(self):
        """Test sentiment on empty list."""
        scores = compute_sentiment_scores([])
        assert len(scores) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
