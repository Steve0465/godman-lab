"""Code Executor Tool - Run Python, Bash, JavaScript code safely."""

from typing import Any, Dict
import subprocess
import tempfile
import os


class CodeExecutorTool:
    """Execute code in multiple languages."""
    
    name = "code_executor"
    description = "Execute Python, Bash, JavaScript, or other code"
    
    def run(self, language: str, code: str, timeout: int = 30, **kwargs) -> Dict[str, Any]:
        """
        Execute code in the specified language.
        
        Args:
            language: 'python', 'bash', 'javascript', 'node'
            code: Code to execute
            timeout: Execution timeout in seconds
            
        Returns:
            Dict with execution results
        """
        executors = {
            "python": self._run_python,
            "bash": self._run_bash,
            "javascript": self._run_javascript,
            "node": self._run_javascript
        }
        
        if language in executors:
            return executors[language](code, timeout)
        else:
            return {"error": f"Unsupported language: {language}"}
    
    def _run_python(self, code: str, timeout: int) -> Dict[str, Any]:
        """Execute Python code."""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            result = subprocess.run(
                ['python3', temp_file],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            os.unlink(temp_file)
            
            return {
                "success": result.returncode == 0,
                "language": "python",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"error": "Execution timed out", "language": "python"}
        except Exception as e:
            return {"error": f"Python execution failed: {str(e)}"}
    
    def _run_bash(self, code: str, timeout: int) -> Dict[str, Any]:
        """Execute Bash code."""
        try:
            result = subprocess.run(
                ['bash', '-c', code],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                "success": result.returncode == 0,
                "language": "bash",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"error": "Execution timed out", "language": "bash"}
        except Exception as e:
            return {"error": f"Bash execution failed: {str(e)}"}
    
    def _run_javascript(self, code: str, timeout: int) -> Dict[str, Any]:
        """Execute JavaScript code using Node.js."""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            result = subprocess.run(
                ['node', temp_file],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            os.unlink(temp_file)
            
            return {
                "success": result.returncode == 0,
                "language": "javascript",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"error": "Execution timed out", "language": "javascript"}
        except FileNotFoundError:
            return {"error": "Node.js not installed"}
        except Exception as e:
            return {"error": f"JavaScript execution failed: {str(e)}"}
