"""
Reviewer Agent

Validates execution outputs and determines if replanning is needed.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class ReviewerAgent:
    """
    Reviews execution outputs for accuracy, consistency, and completeness.
    
    Provides feedback and triggers replanning when needed.
    """
    
    def __init__(self, strictness: str = "medium"):
        """
        Initialize the reviewer agent.
        
        Args:
            strictness: Review strictness level (low, medium, high)
        """
        self.strictness = strictness
        logger.debug(f"ReviewerAgent initialized with strictness: {strictness}")
    
    def review_output(self, step: Dict[str, Any], execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Review execution output for quality and correctness.
        
        Args:
            step: Original plan step
            execution_result: Result from executor containing:
                - step_id: step identifier
                - success: execution success flag
                - output: execution output
                - error: error message if any
        
        Returns:
            Review result containing:
            - step_id: step identifier
            - approved: whether output is approved
            - feedback: review feedback message
            - needs_revision: whether step needs replanning
        """
        step_id = step.get('id', 'unknown')
        logger.info(f"Reviewing output for step {step_id}")
        
        # Check if execution failed
        if not execution_result.get('success', False):
            error = execution_result.get('error', 'Unknown error')
            logger.warning(f"Step {step_id} execution failed: {error}")
            return {
                'step_id': step_id,
                'approved': False,
                'feedback': f"Execution failed: {error}",
                'needs_revision': True
            }
        
        output = execution_result.get('output')
        expected_output = step.get('expected_output', '')
        
        # Perform quality checks
        checks = {
            'completeness': self._check_completeness(output, expected_output),
            'accuracy': self._check_accuracy(output, step),
            'consistency': self._check_consistency(output, step)
        }
        
        logger.debug(f"Quality checks for {step_id}: {checks}")
        
        # Determine approval based on checks and strictness
        approved, feedback, needs_revision = self._evaluate_checks(checks, step_id)
        
        logger.info(f"Step {step_id} review complete: approved={approved}, needs_revision={needs_revision}")
        
        return {
            'step_id': step_id,
            'approved': approved,
            'feedback': feedback,
            'needs_revision': needs_revision
        }
    
    def _check_completeness(self, output: Any, expected_output: str) -> Dict[str, Any]:
        """
        Check if output is complete based on expectations.
        
        Args:
            output: Actual execution output
            expected_output: Description of expected output
        
        Returns:
            Check result with passed flag and details
        """
        if output is None:
            return {
                'passed': False,
                'message': 'Output is None'
            }
        
        if isinstance(output, str) and len(output.strip()) == 0:
            return {
                'passed': False,
                'message': 'Output is empty'
            }
        
        if isinstance(output, (list, dict)) and len(output) == 0:
            return {
                'passed': False,
                'message': 'Output is empty collection'
            }
        
        return {
            'passed': True,
            'message': 'Output is complete'
        }
    
    def _check_accuracy(self, output: Any, step: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if output appears accurate for the given step type.
        
        Args:
            output: Actual execution output
            step: Plan step with action type and context
        
        Returns:
            Check result with passed flag and details
        """
        action_type = step.get('action_type', '')
        
        # Action-specific accuracy checks
        if action_type == 'ocr':
            if isinstance(output, str) and len(output) > 10:
                return {'passed': True, 'message': 'OCR output appears valid'}
            return {'passed': False, 'message': 'OCR output too short or invalid'}
        
        elif action_type == 'classify':
            if output and isinstance(output, (str, dict)):
                return {'passed': True, 'message': 'Classification output valid'}
            return {'passed': False, 'message': 'Classification output invalid'}
        
        elif action_type == 'parse':
            if isinstance(output, (dict, list)):
                return {'passed': True, 'message': 'Parsed data structure valid'}
            return {'passed': False, 'message': 'Parsed data should be dict or list'}
        
        # Default: assume valid if not None
        return {
            'passed': output is not None,
            'message': 'Output present' if output is not None else 'Output missing'
        }
    
    def _check_consistency(self, output: Any, step: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if output is consistent with step requirements.
        
        Args:
            output: Actual execution output
            step: Plan step with requirements
        
        Returns:
            Check result with passed flag and details
        """
        # Basic consistency: output type should match action type expectations
        action_type = step.get('action_type', '')
        
        if action_type in ['summarize', 'classify', 'ocr']:
            if isinstance(output, str):
                return {'passed': True, 'message': 'Output type consistent'}
            return {'passed': False, 'message': f'{action_type} should return string'}
        
        elif action_type == 'parse':
            if isinstance(output, (dict, list)):
                return {'passed': True, 'message': 'Output type consistent'}
            return {'passed': False, 'message': 'Parse should return structured data'}
        
        # Default: pass
        return {'passed': True, 'message': 'Consistency check passed'}
    
    def _evaluate_checks(self, checks: Dict[str, Dict[str, Any]], step_id: str) -> tuple[bool, str, bool]:
        """
        Evaluate quality checks and determine approval status.
        
        Args:
            checks: Dictionary of check results
            step_id: Step identifier for logging
        
        Returns:
            Tuple of (approved, feedback, needs_revision)
        """
        failed_checks = [
            name for name, result in checks.items()
            if not result.get('passed', False)
        ]
        
        if not failed_checks:
            return True, "All quality checks passed", False
        
        # Determine severity based on strictness
        if self.strictness == "low":
            # Low strictness: only fail if all checks fail
            if len(failed_checks) == len(checks):
                feedback = f"All checks failed: {', '.join(failed_checks)}"
                return False, feedback, True
            else:
                feedback = f"Some checks failed but within tolerance: {', '.join(failed_checks)}"
                return True, feedback, False
        
        elif self.strictness == "high":
            # High strictness: fail if any check fails
            feedback = f"Failed checks: {', '.join(failed_checks)}"
            return False, feedback, True
        
        else:  # medium
            # Medium strictness: fail if more than half checks fail
            if len(failed_checks) > len(checks) / 2:
                feedback = f"Too many checks failed: {', '.join(failed_checks)}"
                return False, feedback, True
            else:
                feedback = f"Minor issues in: {', '.join(failed_checks)}"
                return True, feedback, False
