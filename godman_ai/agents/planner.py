"""
Planner Agent

Breaks down high-level user goals into structured execution plans.
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class PlannerAgent:
    """
    Generates structured execution plans from high-level task inputs.
    
    Each plan consists of steps with:
    - id: unique step identifier
    - action_type: type of action (ocr, parse, summarize, classify, execute_tool)
    - input: input data or file path
    - expected_output: description of expected result
    """
    
    def __init__(self, llm_provider: Optional[str] = "openai"):
        """
        Initialize the planner agent.
        
        Args:
            llm_provider: LLM provider to use for plan generation
        """
        self.llm_provider = llm_provider
        logger.debug(f"PlannerAgent initialized with provider: {llm_provider}")
    
    def generate_plan(self, task_input: Any) -> List[Dict[str, Any]]:
        """
        Generate a structured plan from task input.
        
        Args:
            task_input: High-level goal (string, file path, or structured data)
        
        Returns:
            List of plan steps, each containing:
            - id: step identifier
            - action_type: type of action to perform
            - input: input for the step
            - expected_output: description of expected result
        """
        logger.info(f"Generating plan for task: {str(task_input)[:100]}...")
        
        # Lazy import to avoid heavy dependencies
        import os
        
        # Determine input type
        input_type = self._detect_input_type(task_input)
        logger.debug(f"Detected input type: {input_type}")
        
        # Generate plan based on input type
        plan = self._create_plan_for_type(input_type, task_input)
        
        # Validate plan quality
        if not plan or len(plan) == 0:
            logger.warning("Generated plan is empty, attempting regeneration")
            plan = self._create_plan_for_type(input_type, task_input, retry=True)
        
        if not plan:
            logger.error("Failed to generate valid plan after retry")
            raise ValueError("Unable to generate a valid plan for the given input")
        
        logger.info(f"Successfully generated plan with {len(plan)} steps")
        return plan
    
    def _detect_input_type(self, task_input: Any) -> str:
        """Detect the type of input provided."""
        import os
        
        if isinstance(task_input, str):
            if os.path.isfile(task_input):
                ext = os.path.splitext(task_input)[1].lower()
                if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                    return 'image'
                elif ext == '.pdf':
                    return 'pdf'
                elif ext == '.csv':
                    return 'csv'
                elif ext in ['.txt', '.md']:
                    return 'text_file'
                else:
                    return 'file'
            else:
                return 'text'
        elif isinstance(task_input, dict):
            return 'structured'
        else:
            return 'unknown'
    
    def _create_plan_for_type(self, input_type: str, task_input: Any, retry: bool = False) -> List[Dict[str, Any]]:
        """
        Create a plan based on input type.
        
        This is a simplified version. In production, this would call an LLM
        to generate more sophisticated plans.
        """
        plan = []
        
        if input_type == 'image':
            plan = [
                {
                    'id': 'step_1',
                    'action_type': 'ocr',
                    'input': task_input,
                    'expected_output': 'Extracted text from image'
                },
                {
                    'id': 'step_2',
                    'action_type': 'classify',
                    'input': 'step_1_output',
                    'expected_output': 'Document classification (receipt, invoice, etc.)'
                },
                {
                    'id': 'step_3',
                    'action_type': 'parse',
                    'input': 'step_1_output',
                    'expected_output': 'Structured data extraction'
                }
            ]
        
        elif input_type == 'pdf':
            plan = [
                {
                    'id': 'step_1',
                    'action_type': 'parse',
                    'input': task_input,
                    'expected_output': 'Extracted text and metadata from PDF'
                },
                {
                    'id': 'step_2',
                    'action_type': 'classify',
                    'input': 'step_1_output',
                    'expected_output': 'Document type classification'
                },
                {
                    'id': 'step_3',
                    'action_type': 'summarize',
                    'input': 'step_1_output',
                    'expected_output': 'Document summary'
                }
            ]
        
        elif input_type == 'text':
            plan = [
                {
                    'id': 'step_1',
                    'action_type': 'classify',
                    'input': task_input,
                    'expected_output': 'Task classification'
                },
                {
                    'id': 'step_2',
                    'action_type': 'execute_tool',
                    'input': task_input,
                    'expected_output': 'Task execution result'
                }
            ]
        
        elif input_type == 'csv':
            plan = [
                {
                    'id': 'step_1',
                    'action_type': 'parse',
                    'input': task_input,
                    'expected_output': 'Parsed CSV data'
                },
                {
                    'id': 'step_2',
                    'action_type': 'summarize',
                    'input': 'step_1_output',
                    'expected_output': 'Data summary and statistics'
                }
            ]
        
        else:
            # Default plan for unknown types
            plan = [
                {
                    'id': 'step_1',
                    'action_type': 'classify',
                    'input': task_input,
                    'expected_output': 'Input classification and analysis'
                }
            ]
        
        return plan
    
    def replan_step(self, original_step: Dict[str, Any], feedback: str) -> Dict[str, Any]:
        """
        Regenerate a specific step based on reviewer feedback.
        
        Args:
            original_step: The step that needs replanning
            feedback: Feedback from the reviewer
        
        Returns:
            Updated step with revised action plan
        """
        logger.info(f"Replanning step {original_step['id']} based on feedback")
        logger.debug(f"Feedback: {feedback}")
        
        # In production, this would use LLM to incorporate feedback
        # For now, we'll create a revised step with modified approach
        revised_step = original_step.copy()
        revised_step['id'] = f"{original_step['id']}_revised"
        revised_step['feedback_incorporated'] = feedback
        
        logger.debug(f"Generated revised step: {revised_step['id']}")
        return revised_step
