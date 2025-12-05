"""Tool graph engine for automatic tool chaining."""

from typing import List, Dict, Any, Optional, Set
import logging

logger = logging.getLogger(__name__)


class ToolNode:
    """Represents a tool in the graph."""
    
    def __init__(self, name: str, input_types: List[str], output_type: str):
        self.name = name
        self.input_types = input_types
        self.output_type = output_type
        self.edges: List[str] = []  # Tool names this can connect to


class ToolGraph:
    """
    Builds and navigates a directed graph of tools based on their input/output types.
    
    Enables automatic tool chaining for complex multi-step tasks.
    """

    def __init__(self):
        self.nodes: Dict[str, ToolNode] = {}
        self.built = False

    def build_graph(self, orchestrator):
        """
        Build the tool graph from registered tools in the orchestrator.
        
        Args:
            orchestrator: The Orchestrator instance with registered tools
        """
        logger.info("Building tool graph...")
        
        # Clear existing graph
        self.nodes.clear()
        
        # Get all registered tools
        if not hasattr(orchestrator, 'tools'):
            logger.warning("Orchestrator has no tools attribute")
            return
        
        # Build nodes
        for tool_name, tool_cls in orchestrator.tools.items():
            try:
                # Get tool metadata
                input_types = self._get_tool_input_types(tool_cls)
                output_type = self._get_tool_output_type(tool_cls)
                
                node = ToolNode(tool_name, input_types, output_type)
                self.nodes[tool_name] = node
                
                logger.debug(f"Added node: {tool_name} (in: {input_types}, out: {output_type})")
            except Exception as e:
                logger.warning(f"Could not add tool {tool_name} to graph: {e}")
        
        # Build edges (connections between tools)
        for node_name, node in self.nodes.items():
            for other_name, other_node in self.nodes.items():
                if node_name == other_name:
                    continue
                
                # Can connect if this node's output matches other's input
                if node.output_type in other_node.input_types:
                    node.edges.append(other_name)
        
        self.built = True
        logger.info(f"Tool graph built with {len(self.nodes)} nodes")

    def _get_tool_input_types(self, tool_cls) -> List[str]:
        """Extract input types from tool class."""
        # Check for explicit metadata
        if hasattr(tool_cls, 'input_types'):
            return tool_cls.input_types
        
        # Infer from tool name or description
        name = getattr(tool_cls, 'name', tool_cls.__name__).lower()
        
        if 'ocr' in name or 'vision' in name:
            return ['image', 'pdf']
        elif 'parse' in name:
            return ['text', 'json']
        elif 'classify' in name:
            return ['text']
        elif 'summarize' in name:
            return ['text']
        else:
            return ['text']  # Default

    def _get_tool_output_type(self, tool_cls) -> str:
        """Extract output type from tool class."""
        # Check for explicit metadata
        if hasattr(tool_cls, 'output_type'):
            return tool_cls.output_type
        
        # Infer from tool name
        name = getattr(tool_cls, 'name', tool_cls.__name__).lower()
        
        if 'ocr' in name:
            return 'text'
        elif 'classify' in name:
            return 'classification'
        elif 'parse' in name:
            return 'structured_data'
        else:
            return 'text'  # Default

    def suggest_chain(self, task_input: Any) -> List[str]:
        """
        Suggest a chain of tools to process the given input.
        
        Args:
            task_input: The input object (file path, text, etc.)
            
        Returns:
            List of tool names in execution order
        """
        if not self.built:
            logger.warning("Graph not built yet")
            return []
        
        # Detect input type
        input_type = self._detect_input_type(task_input)
        logger.debug(f"Detected input type: {input_type}")
        
        # Find tools that can handle this input type
        starting_tools = [
            name for name, node in self.nodes.items()
            if input_type in node.input_types
        ]
        
        if not starting_tools:
            logger.warning(f"No tools found for input type: {input_type}")
            return []
        
        # For now, return simple single-step chains
        # TODO: Implement multi-step path finding (BFS/DFS)
        return starting_tools[:1]  # Return first matching tool

    def _detect_input_type(self, task_input: Any) -> str:
        """Detect the type of input."""
        if isinstance(task_input, str):
            # Check if it's a file path
            lower = task_input.lower()
            if any(ext in lower for ext in ['.jpg', '.jpeg', '.png', '.gif']):
                return 'image'
            elif '.pdf' in lower:
                return 'pdf'
            elif '.csv' in lower:
                return 'csv'
            elif '.json' in lower:
                return 'json'
            else:
                return 'text'
        
        return 'unknown'

    def find_path(self, start_type: str, end_type: str) -> Optional[List[str]]:
        """
        Find a path from a starting input type to a desired output type.
        
        Args:
            start_type: Input type (e.g., 'image')
            end_type: Desired output type (e.g., 'structured_data')
            
        Returns:
            List of tool names representing the path, or None if no path exists
        """
        if not self.built:
            return None
        
        # Find starting nodes
        start_nodes = [
            name for name, node in self.nodes.items()
            if start_type in node.input_types
        ]
        
        if not start_nodes:
            return None
        
        # BFS to find shortest path
        from collections import deque
        
        for start_node in start_nodes:
            queue = deque([(start_node, [start_node])])
            visited: Set[str] = {start_node}
            
            while queue:
                current, path = queue.popleft()
                current_node = self.nodes[current]
                
                # Check if we reached the goal
                if current_node.output_type == end_type:
                    return path
                
                # Explore neighbors
                for neighbor in current_node.edges:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append((neighbor, path + [neighbor]))
        
        return None

    def execute_chain(self, chain: List[str], input_obj: Any, orchestrator) -> Any:
        """
        Execute a chain of tools sequentially.
        
        Args:
            chain: List of tool names to execute in order
            input_obj: Initial input object
            orchestrator: Orchestrator instance to execute tools
            
        Returns:
            Final output from the last tool in the chain
        """
        if not chain:
            return None
        
        logger.info(f"Executing tool chain: {' -> '.join(chain)}")
        
        current_output = input_obj
        
        for tool_name in chain:
            try:
                logger.debug(f"Executing tool: {tool_name}")
                current_output = orchestrator.run_task(current_output)
            except Exception as e:
                logger.error(f"Error executing {tool_name}: {e}")
                raise
        
        return current_output

    def summary(self) -> Dict[str, Any]:
        """
        Get a summary of the tool graph.
        
        Returns:
            dict: Graph statistics and structure
        """
        if not self.built:
            return {"built": False}
        
        total_edges = sum(len(node.edges) for node in self.nodes.values())
        
        return {
            "built": True,
            "total_nodes": len(self.nodes),
            "total_edges": total_edges,
            "tools": {
                name: {
                    "input_types": node.input_types,
                    "output_type": node.output_type,
                    "connections": len(node.edges),
                }
                for name, node in self.nodes.items()
            }
        }
