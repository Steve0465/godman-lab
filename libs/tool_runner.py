"""
ToolRunner - Function registry and execution framework

Provides decorator-based function registration with schema validation,
subprocess execution, comprehensive logging, and error handling.
"""

import json
import logging
import subprocess
import time
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Union


class ToolRunner:
    """
    Function registry and execution manager.
    
    Features:
    - Decorator-based function registration (@tool)
    - Parameter schema validation
    - Subprocess execution for Python scripts and CLI tools
    - Structured JSON output
    - Comprehensive logging with timing
    
    Example:
        runner = ToolRunner()
        
        @runner.tool(schema={"name": str, "count": int})
        def greet(name: str, count: int = 1):
            return {"message": f"Hello {name}!" * count}
        
        result = runner.run("greet", {"name": "World", "count": 2})
    """
    
    def __init__(self, log_path: Optional[str] = None):
        """
        Initialize ToolRunner.
        
        Args:
            log_path: Path to log file. Defaults to ~/godman-lab/logs/tool_runner.log
        """
        self._registry: Dict[str, Dict[str, Any]] = {}
        
        # Setup logging
        if log_path is None:
            log_path = str(Path.home() / "godman-lab" / "logs" / "tool_runner.log")
        
        Path(log_path).parent.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger("ToolRunner")
        self.logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # File handler
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.info("ToolRunner initialized")
    
    def tool(
        self,
        name: Optional[str] = None,
        schema: Optional[Dict[str, type]] = None,
        description: Optional[str] = None,
        command: Optional[str] = None
    ) -> Callable:
        """
        Decorator to register a function or command as a tool.
        
        Args:
            name: Tool name. If None, uses function name
            schema: Parameter schema {param_name: type}
            description: Tool description
            command: Shell command template. Use {param} for substitution
        
        Returns:
            Decorated function
        
        Example:
            @runner.tool(schema={"path": str}, command="ls -la {path}")
            def list_files(path: str):
                pass
        """
        def decorator(func: Callable) -> Callable:
            tool_name = name or func.__name__
            
            self._registry[tool_name] = {
                "function": func,
                "schema": schema or {},
                "description": description or func.__doc__ or "",
                "command": command
            }
            
            self.logger.info(f"Registered tool: {tool_name}")
            
            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            
            return wrapper
        
        return decorator
    
    def _validate_parameters(
        self,
        function_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate parameters against registered schema.
        
        Args:
            function_name: Name of the function
            parameters: Parameters to validate
        
        Returns:
            Validation result with status and errors
        
        Raises:
            ValueError: If function not found or validation fails
        """
        if function_name not in self._registry:
            raise ValueError(f"Function '{function_name}' not registered")
        
        schema = self._registry[function_name]["schema"]
        errors = []
        
        # Check types
        for param_name, param_type in schema.items():
            if param_name in parameters:
                value = parameters[param_name]
                if not isinstance(value, param_type):
                    errors.append(
                        f"Parameter '{param_name}' must be {param_type.__name__}, "
                        f"got {type(value).__name__}"
                    )
        
        if errors:
            raise ValueError("; ".join(errors))
        
        return {"valid": True, "errors": []}
    
    def _execute_command(
        self,
        command: str,
        parameters: Dict[str, Any],
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Execute a shell command with parameter substitution.
        
        Args:
            command: Command template with {param} placeholders
            parameters: Parameters for substitution
            timeout: Command timeout in seconds
        
        Returns:
            Execution result
        """
        try:
            # Substitute parameters
            formatted_command = command.format(**parameters)
            
            self.logger.info(f"Executing command: {formatted_command}")
            
            # Execute command
            result = subprocess.run(
                formatted_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "success": result.returncode == 0
            }
        
        except subprocess.TimeoutExpired as e:
            self.logger.error(f"Command timeout: {e}")
            return {
                "stdout": "",
                "stderr": f"Command timed out after {timeout} seconds",
                "returncode": -1,
                "success": False
            }
        
        except Exception as e:
            self.logger.error(f"Command execution error: {e}")
            return {
                "stdout": "",
                "stderr": str(e),
                "returncode": -1,
                "success": False
            }
    
    def _execute_function(
        self,
        function: Callable,
        parameters: Dict[str, Any]
    ) -> Any:
        """
        Execute a registered Python function.
        
        Args:
            function: Function to execute
            parameters: Function parameters
        
        Returns:
            Function result
        """
        return function(**parameters)
    
    def run(
        self,
        function_name: str,
        parameters: Optional[Dict[str, Any]] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Execute a registered tool by name.
        
        Args:
            function_name: Name of the registered tool
            parameters: Tool parameters
            timeout: Execution timeout in seconds
        
        Returns:
            JSON result:
            {
                "status": "success" | "error",
                "result": {...},
                "error": {...},
                "execution_time": float,
                "timestamp": str
            }
        
        Example:
            result = runner.run("greet", {"name": "World"})
            if result["status"] == "success":
                print(result["result"])
        """
        parameters = parameters or {}
        start_time = time.time()
        timestamp = datetime.now().isoformat()
        
        # Log invocation
        self.logger.info(
            f"Invocation: function={function_name}, "
            f"parameters={json.dumps(parameters)}"
        )
        
        try:
            # Validate parameters
            self._validate_parameters(function_name, parameters)
            
            tool_info = self._registry[function_name]
            
            # Execute command or function
            if tool_info["command"]:
                exec_result = self._execute_command(
                    tool_info["command"],
                    parameters,
                    timeout
                )
                
                if not exec_result["success"]:
                    raise RuntimeError(
                        f"Command failed: {exec_result['stderr']}"
                    )
                
                result = {
                    "stdout": exec_result["stdout"],
                    "stderr": exec_result["stderr"],
                    "returncode": exec_result["returncode"]
                }
            else:
                result = self._execute_function(
                    tool_info["function"],
                    parameters
                )
            
            execution_time = time.time() - start_time
            
            response = {
                "status": "success",
                "result": result,
                "error": None,
                "execution_time": round(execution_time, 3),
                "timestamp": timestamp
            }
            
            self.logger.info(
                f"Success: function={function_name}, "
                f"time={execution_time:.3f}s, "
                f"result={json.dumps(result, default=str)[:200]}"
            )
            
            return response
        
        except Exception as e:
            execution_time = time.time() - start_time
            
            error_info = {
                "type": type(e).__name__,
                "message": str(e),
                "function": function_name,
                "parameters": parameters
            }
            
            response = {
                "status": "error",
                "result": None,
                "error": error_info,
                "execution_time": round(execution_time, 3),
                "timestamp": timestamp
            }
            
            self.logger.error(
                f"Error: function={function_name}, "
                f"error={error_info['type']}, "
                f"message={error_info['message']}"
            )
            
            return response
    
    def list_tools(self) -> Dict[str, Dict[str, Any]]:
        """
        List all registered tools.
        
        Returns:
            Dictionary of tool names and their metadata
        """
        tools = {}
        for name, info in self._registry.items():
            tools[name] = {
                "name": name,
                "description": info["description"],
                "schema": {
                    param: typ.__name__ 
                    for param, typ in info["schema"].items()
                },
                "has_command": info["command"] is not None
            }
        return tools
    
    def get_tool_info(self, function_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific tool.
        
        Args:
            function_name: Name of the tool
        
        Returns:
            Tool metadata or None if not found
        """
        if function_name not in self._registry:
            return None
        
        info = self._registry[function_name]
        return {
            "name": function_name,
            "description": info["description"],
            "schema": {
                param: typ.__name__ 
                for param, typ in info["schema"].items()
            },
            "command": info["command"],
            "has_command": info["command"] is not None
        }


# Global runner instance
runner = ToolRunner()
tool = runner.tool
