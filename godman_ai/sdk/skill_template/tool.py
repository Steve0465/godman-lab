"""Example Tool Template for GodmanAI Skills"""

from godman_ai.engine import BaseTool


class ExampleTool(BaseTool):
    """Example tool template for custom skill development."""
    
    name = "example_tool"
    description = "Example tool template."

    def run(self, **kwargs):
        """
        Execute the tool with provided arguments.
        
        Args:
            **kwargs: Arbitrary keyword arguments
            
        Returns:
            dict: Result containing message and input echo
        """
        return {"message": "Example tool executed.", "input": kwargs}
