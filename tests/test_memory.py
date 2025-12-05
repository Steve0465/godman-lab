"""
Tests for memory subsystem (vector store, episodic memory, working memory).
"""
import pytest
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def temp_storage():
    """Create temporary storage directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_working_memory():
    """Test working memory storage and retrieval."""
    from godman_ai.memory import WorkingMemory
    
    memory = WorkingMemory()
    
    # Test push and get
    memory.push("key1", "value1")
    assert memory.get("key1") == "value1"
    
    # Test default value
    assert memory.get("nonexistent", "default") == "default"
    
    # Test has
    assert memory.has("key1") is True
    assert memory.has("nonexistent") is False
    
    # Test pop
    value = memory.pop("key1")
    assert value == "value1"
    assert memory.has("key1") is False
    
    # Test update
    memory.update({"a": 1, "b": 2})
    assert memory.get("a") == 1
    assert memory.get("b") == 2
    
    # Test clear
    memory.clear()
    assert len(list(memory.keys())) == 0


def test_episodic_memory(temp_storage):
    """Test episodic memory storage and recall."""
    from godman_ai.memory import EpisodicMemory
    
    store_path = Path(temp_storage) / "episodic"
    memory = EpisodicMemory(store_path=str(store_path))
    
    # Add episode
    task_input = "Process receipt from grocery store"
    plan = [{"id": 1, "action": "ocr"}]
    results = {"final_output": "Receipt processed successfully"}
    
    memory.add_episode(task_input, plan, results)
    
    # Check file created
    assert memory.episodes_file.exists()
    
    # Get recent episodes
    recent = memory.get_recent(limit=10)
    assert len(recent) == 1
    assert recent[0]['task_input'] == task_input


def test_vector_store_basic(temp_storage):
    """Test basic vector store operations without OpenAI."""
    from godman_ai.memory import VectorStore
    
    store_path = Path(temp_storage) / "vector"
    store = VectorStore(store_path=str(store_path))
    
    # Test initialization
    assert store.store_path.exists()
    
    # Note: Without OpenAI API key, embeddings will be zero vectors
    # This is just testing the structure, not functionality
    assert store.dimension == 1536


def test_episodic_memory_clear(temp_storage):
    """Test clearing episodic memory."""
    from godman_ai.memory import EpisodicMemory
    
    store_path = Path(temp_storage) / "episodic"
    memory = EpisodicMemory(store_path=str(store_path))
    
    # Add episodes
    memory.add_episode("task1", [], {})
    memory.add_episode("task2", [], {})
    
    assert len(memory.get_recent()) == 2
    
    # Clear
    memory.clear()
    assert len(memory.get_recent()) == 0
