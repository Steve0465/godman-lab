"""
Executor Agent

Executes individual plan steps using tools, LLM reasoning, or Python functions.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ExecutorAgent:
    """
    Executes individual plan steps by routing to appropriate execution methods.
    
    Supports:
    - Tool execution via Orchestrator
    - Direct LLM reasoning
    - Inline Python functions
    """
    
    def __init__(self):
        """Initialize the executor agent with lazy-loaded dependencies."""
        self._orchestrator = None
        logger.debug("ExecutorAgent initialized")
    
    @property
    def orchestrator(self):
        """Lazy-load orchestrator to avoid heavy imports at module level."""
        if self._orchestrator is None:
            from godman_ai.orchestrator import Orchestrator
            self._orchestrator = Orchestrator()
            self._orchestrator.load_tools_from_package("godman_ai.tools")
            logger.debug("Orchestrator loaded lazily")
        return self._orchestrator
    
    def execute_step(self, step: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a single plan step.
        
        Args:
            step: Plan step containing:
                - id: step identifier
                - action_type: type of action to perform
                - input: input data for the step
                - expected_output: description of expected result
            context: Optional execution context with previous step outputs
        
        Returns:
            Execution result containing:
            - step_id: identifier of the executed step
            - success: whether execution succeeded
            - output: execution output data
            - error: error message if execution failed
        """
        step_id = step.get('id', 'unknown')
        action_type = step.get('action_type', 'unknown')
        step_input = step.get('input')
        
        logger.info(f"Executing step {step_id} with action type: {action_type}")
        
        try:
            # Resolve input from context if it references previous step
            resolved_input = self._resolve_input(step_input, context)
            
            # Route to appropriate execution method
            if action_type in ['ocr', 'parse', 'classify', 'execute_tool']:
                output = self._execute_via_orchestrator(resolved_input, action_type)
            elif action_type == 'summarize':
                output = self._execute_via_llm(resolved_input, action_type)
            else:
                output = self._execute_inline(resolved_input, action_type)
            
            logger.info(f"Step {step_id} executed successfully")
            return {
                'step_id': step_id,
                'success': True,
                'output': output,
                'error': None
            }
        
        except Exception as e:
            logger.error(f"Step {step_id} failed: {str(e)}", exc_info=True)
            return {
                'step_id': step_id,
                'success': False,
                'output': None,
                'error': str(e)
            }
    
    def _resolve_input(self, step_input: Any, context: Optional[Dict[str, Any]]) -> Any:
        """
        Resolve step input, replacing references to previous step outputs.
        
        Args:
            step_input: Raw input from plan step
            context: Execution context with previous outputs
        
        Returns:
            Resolved input value
        """
        if context is None:
            return step_input
        
        # Check if input references a previous step output
        if isinstance(step_input, str) and step_input.endswith('_output'):
            ref_step_id = step_input.replace('_output', '')
            if ref_step_id in context:
                logger.debug(f"Resolved input reference {step_input} from context")
                return context[ref_step_id]
        
        return step_input
    
    def _execute_via_orchestrator(self, resolved_input: Any, action_type: str) -> Any:
        """
        Execute step using the Orchestrator and its registered tools.
        
        Args:
            resolved_input: Resolved input data
            action_type: Type of action to perform
        
        Returns:
            Tool execution output
        """
        logger.debug(f"Executing via orchestrator: {action_type}")
        
        try:
            result = self.orchestrator.run_task(resolved_input)
            return result
        except Exception as e:
            logger.error(f"Orchestrator execution failed: {str(e)}")
            raise
    
    def _execute_via_llm(self, resolved_input: Any, action_type: str) -> str:
        """
        Execute step using direct LLM reasoning.
        
        Args:
            resolved_input: Resolved input data
            action_type: Type of action to perform
        
        Returns:
            LLM-generated output
        """
        logger.debug(f"Executing via LLM: {action_type}")
        
        # Lazy import OpenAI
        try:
            import os
            import openai
            
            openai.api_key = os.getenv('OPENAI_API_KEY')
            
            if not openai.api_key:
                logger.warning("OpenAI API key not found, using mock response")
                return f"[Mock {action_type}] Processed: {str(resolved_input)[:100]}"
            
            # Create appropriate prompt based on action type
            if action_type == 'summarize':
                prompt = f"Summarize the following:\n\n{resolved_input}"
            else:
                prompt = f"Perform {action_type} on:\n\n{resolved_input}"
            
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": f"You are a helpful assistant that performs {action_type} tasks."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            output = response.choices[0].message.content
            logger.debug(f"LLM response received: {len(output)} characters")
            return output
        
        except ImportError:
            logger.warning("OpenAI library not available, using mock response")
            return f"[Mock {action_type}] Processed: {str(resolved_input)[:100]}"
        except Exception as e:
            logger.error(f"LLM execution failed: {str(e)}")
            raise
    
    def _execute_inline(self, resolved_input: Any, action_type: str) -> Any:
        """
        Execute step using inline Python function.
        
        Args:
            resolved_input: Resolved input data
            action_type: Type of action to perform
        
        Returns:
            Function execution output
        """
        logger.debug(f"Executing inline: {action_type}")
        
        # Simple inline handlers for common operations
        if action_type == 'count':
            if isinstance(resolved_input, (list, str)):
                return len(resolved_input)
            return 1
        
        elif action_type == 'format':
            return str(resolved_input).strip()
        
        else:
            logger.warning(f"Unknown inline action type: {action_type}")
            return resolved_input
