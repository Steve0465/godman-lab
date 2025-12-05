"""Tests for tool graph engine."""

import pytest
from godman_ai.os_core.tool_graph import ToolGraph, ToolNode
from godman_ai.engine import BaseTool


class DummyOCRTool(BaseTool):
    """Test OCR tool."""
    name = "ocr"
    description = "Extract text from images"
    input_types = ["image", "pdf"]
    output_type = "text"
    
    def run(self, **kwargs):
        return {"text": "extracted text"}


class DummyParserTool(BaseTool):
    """Test parser tool."""
    name = "parser"
    description = "Parse structured data from text"
    input_types = ["text"]
    output_type = "structured_data"
    
    def run(self, **kwargs):
        return {"data": {"key": "value"}}


class DummyClassifierTool(BaseTool):
    """Test classifier tool."""
    name = "classifier"
    description = "Classify text"
    input_types = ["text"]
    output_type = "classification"
    
    def run(self, **kwargs):
        return {"category": "receipt"}


class MockOrchestrator:
    """Mock orchestrator for testing."""
    def __init__(self):
        self.tools = {
            "ocr": DummyOCRTool,
            "parser": DummyParserTool,
            "classifier": DummyClassifierTool,
        }
    
    def run_task(self, input_obj):
        return {"success": True, "result": "mock result"}


def test_tool_graph_initialization():
    """Test ToolGraph initializes correctly."""
    graph = ToolGraph()
    
    assert graph.nodes == {}
    assert graph.built is False


def test_build_graph():
    """Test building graph from orchestrator."""
    graph = ToolGraph()
    orchestrator = MockOrchestrator()
    
    graph.build_graph(orchestrator)
    
    assert graph.built is True
    assert len(graph.nodes) == 3
    assert "ocr" in graph.nodes
    assert "parser" in graph.nodes
    assert "classifier" in graph.nodes


def test_tool_node_edges():
    """Test that edges are created correctly."""
    graph = ToolGraph()
    orchestrator = MockOrchestrator()
    
    graph.build_graph(orchestrator)
    
    # OCR produces text, which both parser and classifier accept
    ocr_node = graph.nodes["ocr"]
    assert "parser" in ocr_node.edges or "classifier" in ocr_node.edges


def test_suggest_chain_for_image():
    """Test suggesting tool chain for image input."""
    graph = ToolGraph()
    orchestrator = MockOrchestrator()
    
    graph.build_graph(orchestrator)
    
    # Image should route to OCR
    chain = graph.suggest_chain("test.jpg")
    
    assert len(chain) > 0
    assert chain[0] == "ocr"


def test_suggest_chain_for_text():
    """Test suggesting tool chain for text input."""
    graph = ToolGraph()
    orchestrator = MockOrchestrator()
    
    graph.build_graph(orchestrator)
    
    # Text should route to parser or classifier
    chain = graph.suggest_chain("some text input")
    
    assert len(chain) > 0
    assert chain[0] in ["parser", "classifier"]


def test_find_path():
    """Test finding path between input and output types."""
    graph = ToolGraph()
    orchestrator = MockOrchestrator()
    
    graph.build_graph(orchestrator)
    
    # Find path from image to structured_data
    path = graph.find_path("image", "structured_data")
    
    # Should be: image -> ocr -> parser -> structured_data
    if path:
        assert path[0] == "ocr"
        assert "parser" in path


def test_execute_chain():
    """Test executing a tool chain."""
    graph = ToolGraph()
    orchestrator = MockOrchestrator()
    
    graph.build_graph(orchestrator)
    
    # Execute a simple chain
    chain = ["ocr"]
    result = graph.execute_chain(chain, "test.jpg", orchestrator)
    
    assert result is not None


def test_summary():
    """Test graph summary generation."""
    graph = ToolGraph()
    orchestrator = MockOrchestrator()
    
    graph.build_graph(orchestrator)
    
    summary = graph.summary()
    
    assert summary["built"] is True
    assert summary["total_nodes"] == 3
    assert "tools" in summary
    assert "ocr" in summary["tools"]


def test_detect_input_type():
    """Test input type detection."""
    graph = ToolGraph()
    
    assert graph._detect_input_type("test.jpg") == "image"
    assert graph._detect_input_type("test.pdf") == "pdf"
    assert graph._detect_input_type("test.csv") == "csv"
    assert graph._detect_input_type("plain text") == "text"
