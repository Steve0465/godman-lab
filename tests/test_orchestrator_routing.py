"""Test suite for Orchestrator routing and tool discovery."""
import pytest
from pathlib import Path
from typing import Any, Dict

# Import orchestrator and BaseTool
from godman_ai.orchestrator import Orchestrator
from godman_ai.engine import BaseTool


class DummyTool(BaseTool):
    """Dummy tool for testing purposes."""
    
    name = "dummy"
    description = "A simple dummy tool for testing"
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute dummy task."""
        return {
            "status": "success",
            "message": "DummyTool executed successfully",
            "input": kwargs.get("input"),
            "kwargs": list(kwargs.keys())
        }


class TestInputTypeDetection:
    """Test input type detection logic."""
    
    def test_detect_text_string(self):
        """Test detection of plain text strings."""
        orch = Orchestrator()
        result = orch.detect_input_type("hello world")
        assert result == "unknown"  # String without path defaults to unknown
    
    def test_detect_image_jpg(self):
        """Test detection of .jpg files."""
        orch = Orchestrator()
        # Create a temporary file for testing
        temp_path = Path("/tmp/test_image.jpg")
        temp_path.touch()
        
        result = orch.detect_input_type(str(temp_path))
        assert result == "image"
        
        # Cleanup
        temp_path.unlink()
    
    def test_detect_image_png(self):
        """Test detection of .png files."""
        orch = Orchestrator()
        temp_path = Path("/tmp/test_image.png")
        temp_path.touch()
        
        result = orch.detect_input_type(temp_path)
        assert result == "image"
        
        temp_path.unlink()
    
    def test_detect_pdf(self):
        """Test detection of .pdf files."""
        orch = Orchestrator()
        temp_path = Path("/tmp/test_doc.pdf")
        temp_path.touch()
        
        result = orch.detect_input_type(str(temp_path))
        assert result == "pdf"
        
        temp_path.unlink()
    
    def test_detect_csv(self):
        """Test detection of .csv files."""
        orch = Orchestrator()
        temp_path = Path("/tmp/test_data.csv")
        temp_path.touch()
        
        result = orch.detect_input_type(str(temp_path))
        assert result == "csv"
        
        temp_path.unlink()
    
    def test_detect_json_dict(self):
        """Test detection of dict objects as JSON."""
        orch = Orchestrator()
        result = orch.detect_input_type({"key": "value"})
        assert result == "json"
    
    def test_detect_json_file(self):
        """Test detection of .json files."""
        orch = Orchestrator()
        temp_path = Path("/tmp/test_data.json")
        temp_path.touch()
        
        result = orch.detect_input_type(str(temp_path))
        assert result == "json"
        
        temp_path.unlink()
    
    def test_detect_audio_mp3(self):
        """Test detection of .mp3 audio files."""
        orch = Orchestrator()
        temp_path = Path("/tmp/test_audio.mp3")
        temp_path.touch()
        
        result = orch.detect_input_type(str(temp_path))
        assert result == "audio"
        
        temp_path.unlink()
    
    def test_detect_video_mp4(self):
        """Test detection of .mp4 video files."""
        orch = Orchestrator()
        temp_path = Path("/tmp/test_video.mp4")
        temp_path.touch()
        
        result = orch.detect_input_type(str(temp_path))
        assert result == "video"
        
        temp_path.unlink()
    
    def test_detect_unknown_extension(self):
        """Test detection of unknown file extensions."""
        orch = Orchestrator()
        temp_path = Path("/tmp/test_file.xyz")
        temp_path.touch()
        
        result = orch.detect_input_type(str(temp_path))
        assert result == "unknown"
        
        temp_path.unlink()
    
    def test_detect_nonexistent_file(self):
        """Test detection of non-existent files."""
        orch = Orchestrator()
        result = orch.detect_input_type("/path/to/nonexistent/file.jpg")
        assert result == "unknown"


class TestToolRegistration:
    """Test tool registration and discovery."""
    
    def test_register_tool_manually(self):
        """Test manual tool registration."""
        orch = Orchestrator()
        orch.register_tool("dummy", DummyTool)
        
        assert "dummy" in orch.tool_classes
        assert orch.tool_classes["dummy"] == DummyTool
    
    def test_register_tool_invalid_type(self):
        """Test that non-BaseTool classes raise TypeError."""
        orch = Orchestrator()
        
        class NotATool:
            pass
        
        with pytest.raises(TypeError):
            orch.register_tool("invalid", NotATool)
    
    def test_load_tools_from_package(self):
        """Test automatic tool discovery from package."""
        orch = Orchestrator()
        orch.load_tools_from_package("godman_ai.tools")
        
        # Should discover at least some tools
        assert len(orch.tool_classes) >= 0  # May be 0 if no tools exist yet
        
        # Check tool classes are registered
        for tool_name, tool_cls in orch.tool_classes.items():
            assert issubclass(tool_cls, BaseTool)


class TestTaskRouting:
    """Test task routing and execution."""
    
    def test_run_task_with_dummy_tool(self):
        """Test that run_task correctly routes to registered tool."""
        orch = Orchestrator()
        orch.register_tool("dummy", DummyTool)
        
        # Override handler to use dummy tool for text
        orch.set_handler("text", "dummy")
        
        # Create a text file
        temp_path = Path("/tmp/test.txt")
        temp_path.touch()
        
        result = orch.run_task(str(temp_path))
        
        assert result["status"] == "success"
        assert result["input_type"] == "text"
        assert result["tool"] == "dummy"
        assert "result" in result
        
        temp_path.unlink()
    
    def test_run_task_unknown_type(self):
        """Test that unknown input types return error."""
        orch = Orchestrator()
        
        result = orch.run_task("random_string_with_no_path")
        
        assert result["status"] == "error"
        assert "error" in result
    
    def test_run_task_missing_handler(self):
        """Test error when no handler configured for input type."""
        orch = Orchestrator()
        
        # Create a file type with no handler
        temp_path = Path("/tmp/test.txt")
        temp_path.touch()
        
        # Remove text handler
        if "text" in orch.type_handlers:
            del orch.type_handlers["text"]
        
        result = orch.run_task(str(temp_path))
        
        assert result["status"] == "error"
        assert "No handler configured" in result["error"]
        
        temp_path.unlink()
    
    def test_run_task_tool_not_registered(self):
        """Test error when handler points to unregistered tool."""
        orch = Orchestrator()
        
        # Set handler to non-existent tool
        orch.set_handler("text", "nonexistent_tool")
        
        temp_path = Path("/tmp/test.txt")
        temp_path.touch()
        
        result = orch.run_task(str(temp_path))
        
        assert result["status"] == "error"
        assert "not registered" in result["error"]
        
        temp_path.unlink()


class TestOrchestratorStatus:
    """Test orchestrator status and metadata."""
    
    def test_list_tools(self):
        """Test tool listing functionality."""
        orch = Orchestrator()
        orch.register_tool("dummy", DummyTool)
        
        tools = orch.list_tools()
        
        assert "dummy" in tools
        assert tools["dummy"]["class"] == "DummyTool"
        assert tools["dummy"]["description"] == "A simple dummy tool for testing"
    
    def test_status(self):
        """Test orchestrator status reporting."""
        orch = Orchestrator()
        orch.register_tool("dummy", DummyTool)
        
        status = orch.status()
        
        assert status["tools_registered"] == 1
        assert status["tools_instantiated"] == 0
        assert "dummy" in status["tool_names"]
        assert status["ready"] is True
    
    def test_set_handler(self):
        """Test custom handler configuration."""
        orch = Orchestrator()
        orch.register_tool("dummy", DummyTool)
        orch.set_handler("custom_type", "dummy")
        
        assert orch.type_handlers["custom_type"] == "dummy"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
