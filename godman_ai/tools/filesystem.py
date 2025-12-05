"""File System Tool - Navigate and manipulate files."""

from typing import Any, Dict, List
import os
import shutil
from pathlib import Path


class FileSystemTool:
    """Navigate and manipulate the file system."""
    
    name = "filesystem"
    description = "Read, write, and organize files"
    
    def run(self, action: str, **kwargs) -> Dict[str, Any]:
        """
        Perform file system operations.
        
        Args:
            action: 'read', 'write', 'list', 'move', 'copy', 'delete', 'search'
            **kwargs: Action-specific parameters
            
        Returns:
            Dict with operation results
        """
        actions = {
            "read": self.read_file,
            "write": self.write_file,
            "list": self.list_directory,
            "move": self.move_file,
            "copy": self.copy_file,
            "delete": self.delete_file,
            "search": self.search_files,
            "organize": self.organize_files
        }
        
        if action in actions:
            return actions[action](**kwargs)
        else:
            return {"error": f"Unknown action: {action}"}
    
    def read_file(self, path: str, **kwargs) -> Dict[str, Any]:
        """Read file contents."""
        try:
            path = os.path.expanduser(path)
            with open(path, 'r') as f:
                content = f.read()
            return {
                "success": True,
                "path": path,
                "content": content,
                "size": os.path.getsize(path)
            }
        except Exception as e:
            return {"error": f"Failed to read file: {str(e)}"}
    
    def write_file(self, path: str, content: str, append: bool = False, **kwargs) -> Dict[str, Any]:
        """Write content to a file."""
        try:
            path = os.path.expanduser(path)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            mode = 'a' if append else 'w'
            with open(path, mode) as f:
                f.write(content)
            
            return {
                "success": True,
                "path": path,
                "bytes_written": len(content)
            }
        except Exception as e:
            return {"error": f"Failed to write file: {str(e)}"}
    
    def list_directory(self, path: str = ".", recursive: bool = False, **kwargs) -> Dict[str, Any]:
        """List files in a directory."""
        try:
            path = os.path.expanduser(path)
            files = []
            
            if recursive:
                for root, dirs, filenames in os.walk(path):
                    for filename in filenames:
                        filepath = os.path.join(root, filename)
                        files.append({
                            "path": filepath,
                            "name": filename,
                            "size": os.path.getsize(filepath),
                            "modified": os.path.getmtime(filepath)
                        })
            else:
                for item in os.listdir(path):
                    filepath = os.path.join(path, item)
                    files.append({
                        "path": filepath,
                        "name": item,
                        "is_dir": os.path.isdir(filepath),
                        "size": os.path.getsize(filepath) if os.path.isfile(filepath) else 0
                    })
            
            return {
                "success": True,
                "path": path,
                "count": len(files),
                "files": files
            }
        except Exception as e:
            return {"error": f"Failed to list directory: {str(e)}"}
    
    def move_file(self, source: str, destination: str, **kwargs) -> Dict[str, Any]:
        """Move a file or directory."""
        try:
            source = os.path.expanduser(source)
            destination = os.path.expanduser(destination)
            shutil.move(source, destination)
            return {
                "success": True,
                "source": source,
                "destination": destination
            }
        except Exception as e:
            return {"error": f"Failed to move file: {str(e)}"}
    
    def copy_file(self, source: str, destination: str, **kwargs) -> Dict[str, Any]:
        """Copy a file or directory."""
        try:
            source = os.path.expanduser(source)
            destination = os.path.expanduser(destination)
            
            if os.path.isdir(source):
                shutil.copytree(source, destination)
            else:
                shutil.copy2(source, destination)
            
            return {
                "success": True,
                "source": source,
                "destination": destination
            }
        except Exception as e:
            return {"error": f"Failed to copy file: {str(e)}"}
    
    def delete_file(self, path: str, **kwargs) -> Dict[str, Any]:
        """Delete a file or directory."""
        try:
            path = os.path.expanduser(path)
            
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            
            return {
                "success": True,
                "path": path,
                "deleted": True
            }
        except Exception as e:
            return {"error": f"Failed to delete file: {str(e)}"}
    
    def search_files(self, pattern: str, directory: str = ".", **kwargs) -> Dict[str, Any]:
        """Search for files matching a pattern."""
        try:
            import fnmatch
            
            directory = os.path.expanduser(directory)
            matches = []
            
            for root, dirs, files in os.walk(directory):
                for filename in fnmatch.filter(files, pattern):
                    filepath = os.path.join(root, filename)
                    matches.append({
                        "path": filepath,
                        "name": filename,
                        "size": os.path.getsize(filepath)
                    })
            
            return {
                "success": True,
                "pattern": pattern,
                "directory": directory,
                "count": len(matches),
                "matches": matches
            }
        except Exception as e:
            return {"error": f"Failed to search files: {str(e)}"}
    
    def organize_files(self, directory: str, by: str = "extension", **kwargs) -> Dict[str, Any]:
        """Organize files by extension, date, or type."""
        try:
            directory = os.path.expanduser(directory)
            organized = {}
            
            for filename in os.listdir(directory):
                filepath = os.path.join(directory, filename)
                if os.path.isfile(filepath):
                    if by == "extension":
                        ext = Path(filename).suffix or "no_extension"
                        dest_dir = os.path.join(directory, ext.lstrip('.'))
                    else:
                        dest_dir = os.path.join(directory, "other")
                    
                    os.makedirs(dest_dir, exist_ok=True)
                    dest_path = os.path.join(dest_dir, filename)
                    shutil.move(filepath, dest_path)
                    
                    if ext not in organized:
                        organized[ext] = []
                    organized[ext].append(filename)
            
            return {
                "success": True,
                "directory": directory,
                "organized_by": by,
                "categories": organized
            }
        except Exception as e:
            return {"error": f"Failed to organize files: {str(e)}"}
