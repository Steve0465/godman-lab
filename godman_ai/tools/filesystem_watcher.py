"""
File System Watcher Tool - Auto-processes files as they appear
"""
from ..engine import BaseTool
import time
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class FileSystemWatcherTool(BaseTool):
    """Watch directories and auto-process new files"""
    
    name = "filesystem_watcher"
    description = "Monitors directories for new files and auto-processes them"
    
    def __init__(self):
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
            self.Observer = Observer
            self.FileSystemEventHandler = FileSystemEventHandler
            self.available = True
        except ImportError:
            logger.warning("watchdog not installed. Run: pip install watchdog")
            self.available = False
    
    def run(self, watch_dir: str, patterns: dict = None, **kwargs):
        """
        Watch a directory and trigger actions on new files
        
        Args:
            watch_dir: Directory to watch
            patterns: Dict of {file_pattern: action_callback}
        """
        if not self.available:
            return {"error": "watchdog library not available"}
        
        watch_path = Path(watch_dir)
        if not watch_path.exists():
            return {"error": f"Directory does not exist: {watch_dir}"}
        
        patterns = patterns or {
            "*.pdf": "process_receipt",
            "*.jpg": "ocr_image",
            "*.png": "ocr_image",
        }
        
        class Handler(self.FileSystemEventHandler):
            def on_created(self, event):
                if event.is_directory:
                    return
                
                file_path = Path(event.src_path)
                logger.info(f"New file detected: {file_path}")
                
                # Match pattern and trigger action
                for pattern, action in patterns.items():
                    if file_path.match(pattern):
                        logger.info(f"Matched {pattern} -> triggering {action}")
                        # This would trigger orchestrator or agent
                        return {"file": str(file_path), "action": action}
        
        observer = self.Observer()
        observer.schedule(Handler(), str(watch_path), recursive=True)
        observer.start()
        
        return {
            "status": "watching",
            "directory": str(watch_path),
            "patterns": patterns,
            "observer": observer
        }
