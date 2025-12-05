"""Example Agent Template for GodmanAI Skills"""


class ExampleAgent:
    """
    Example agent template for custom logic.
    
    Agents can implement custom processing workflows that go beyond
    simple tool execution.
    """

    def run(self, task_input):
        """
        Process a task input.
        
        Args:
            task_input: Input data to process
            
        Returns:
            dict: Agent response with processed data
        """
        return {"agent_response": f"Processed: {task_input}"}
