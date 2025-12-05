"""
Agent Loop Controller

Orchestrates the full Planner → Executor → Reviewer cycle.
"""

import logging
from typing import Any, Dict, List, Optional

from .planner import PlannerAgent
from .executor import ExecutorAgent
from .reviewer import ReviewerAgent

logger = logging.getLogger(__name__)


class AgentLoop:
    """
    Main controller for the agent architecture.
    
    Coordinates:
    1. Planning: Generate execution plan from user input
    2. Execution: Execute each step using appropriate tools/methods
    3. Review: Validate outputs and trigger replanning if needed
    """
    
    def __init__(self, max_retries: int = 3, review_strictness: str = "medium"):
        """
        Initialize the agent loop.
        
        Args:
            max_retries: Maximum number of retries per step
            review_strictness: Strictness level for reviewer (low, medium, high)
        """
        self.planner = PlannerAgent()
        self.executor = ExecutorAgent()
        self.reviewer = ReviewerAgent(strictness=review_strictness)
        self.max_retries = max_retries
        
        logger.info(f"AgentLoop initialized (max_retries={max_retries}, strictness={review_strictness})")
    
    def run(self, task_input: Any) -> Dict[str, Any]:
        """
        Execute the full agent loop on the given task input.
        
        Args:
            task_input: User input (file path, text, or structured data)
        
        Returns:
            Execution result containing:
            - final_output: Aggregated output from all steps
            - steps: List of executed steps with their outputs
            - reviews: List of review results for each step
            - raw_plan: Original generated plan
            - success: Overall execution success flag
        """
        logger.info("=" * 60)
        logger.info("AGENT LOOP START")
        logger.info(f"Task input: {str(task_input)[:100]}...")
        logger.info("=" * 60)
        
        try:
            # Phase 1: Planning
            logger.info("Phase 1: PLANNING")
            plan = self.planner.generate_plan(task_input)
            logger.info(f"Generated plan with {len(plan)} steps")
            
            # Phase 2 & 3: Execute and Review each step
            context = {}  # Store outputs for inter-step dependencies
            executed_steps = []
            reviews = []
            
            for step in plan:
                step_id = step.get('id', 'unknown')
                logger.info(f"\nPhase 2: EXECUTING step {step_id}")
                
                # Execute with retry logic
                execution_result, review_result = self._execute_with_retry(step, context)
                
                # Store results
                executed_steps.append({
                    'step': step,
                    'execution': execution_result,
                    'review': review_result
                })
                reviews.append(review_result)
                
                # Update context if execution succeeded
                if execution_result.get('success'):
                    context[step_id] = execution_result.get('output')
                else:
                    logger.error(f"Step {step_id} failed after all retries")
                    # Continue with remaining steps even if one fails
            
            # Aggregate final output
            final_output = self._aggregate_outputs(executed_steps)
            success = all(step['execution'].get('success', False) for step in executed_steps)
            
            logger.info("=" * 60)
            logger.info(f"AGENT LOOP COMPLETE (success={success})")
            logger.info("=" * 60)
            
            return {
                'final_output': final_output,
                'steps': executed_steps,
                'reviews': reviews,
                'raw_plan': plan,
                'success': success
            }
        
        except Exception as e:
            logger.error(f"Agent loop failed: {str(e)}", exc_info=True)
            return {
                'final_output': None,
                'steps': [],
                'reviews': [],
                'raw_plan': [],
                'success': False,
                'error': str(e)
            }
    
    def _execute_with_retry(
        self,
        step: Dict[str, Any],
        context: Dict[str, Any]
    ) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Execute a step with retry logic based on reviewer feedback.
        
        Args:
            step: Plan step to execute
            context: Execution context with previous outputs
        
        Returns:
            Tuple of (execution_result, review_result)
        """
        step_id = step.get('id', 'unknown')
        current_step = step
        
        for attempt in range(self.max_retries):
            logger.debug(f"Attempt {attempt + 1}/{self.max_retries} for step {step_id}")
            
            # Execute step
            execution_result = self.executor.execute_step(current_step, context)
            
            # Review output
            logger.info(f"Phase 3: REVIEWING step {step_id}")
            review_result = self.reviewer.review_output(current_step, execution_result)
            
            # Check if approved
            if review_result.get('approved', False):
                logger.info(f"Step {step_id} approved")
                return execution_result, review_result
            
            # If not approved and needs revision
            if review_result.get('needs_revision', False):
                logger.warning(f"Step {step_id} needs revision: {review_result.get('feedback')}")
                
                # Replan if we haven't exceeded retries
                if attempt < self.max_retries - 1:
                    logger.info(f"Replanning step {step_id}")
                    current_step = self.planner.replan_step(
                        current_step,
                        review_result.get('feedback', '')
                    )
                else:
                    logger.error(f"Step {step_id} failed after {self.max_retries} attempts")
        
        # Return last attempt's results if all retries exhausted
        return execution_result, review_result
    
    def _aggregate_outputs(self, executed_steps: List[Dict[str, Any]]) -> Any:
        """
        Aggregate outputs from all executed steps into final result.
        
        Args:
            executed_steps: List of executed step results
        
        Returns:
            Aggregated final output
        """
        if not executed_steps:
            return None
        
        # If only one step, return its output directly
        if len(executed_steps) == 1:
            return executed_steps[0]['execution'].get('output')
        
        # Multiple steps: create structured output
        aggregated = {
            'summary': {},
            'outputs': []
        }
        
        successful_steps = 0
        for step_result in executed_steps:
            step = step_result['step']
            execution = step_result['execution']
            
            step_id = step.get('id', 'unknown')
            success = execution.get('success', False)
            output = execution.get('output')
            
            if success:
                successful_steps += 1
            
            aggregated['outputs'].append({
                'step_id': step_id,
                'action_type': step.get('action_type'),
                'success': success,
                'output': output
            })
        
        aggregated['summary'] = {
            'total_steps': len(executed_steps),
            'successful_steps': successful_steps,
            'success_rate': successful_steps / len(executed_steps) if executed_steps else 0
        }
        
        logger.debug(f"Aggregated {len(executed_steps)} step outputs")
        return aggregated
