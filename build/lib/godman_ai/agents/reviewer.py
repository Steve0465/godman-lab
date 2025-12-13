"""
Reviewer Agent - Reviews execution results for quality and correctness.

The ReviewerAgent validates execution outputs, checks for errors,
and provides approval or feedback for improvement.
"""

from dataclasses import dataclass, field
from typing import Dict, List
import re


@dataclass
class AgentResponse:
    """
    Standard response format for all agents.
    
    Attributes:
        content: Main response content (text, plan, result, etc.)
        metadata: Additional context and information about the response
    """
    content: str
    metadata: Dict = field(default_factory=dict)


class ReviewerAgent:
    """
    Reviewer agent that validates execution results.
    
    The reviewer checks outputs for errors, completeness, and quality,
    providing approval or requesting revisions.
    """
    
    def __init__(self, agent_id: str = "reviewer-001"):
        """
        Initialize the ReviewerAgent.
        
        Args:
            agent_id: Unique identifier for this agent instance
        """
        self.agent_id = agent_id
        self.reviews_completed = 0
        self.approvals = 0
        self.rejections = 0
    
    def review(self, execution_output: str) -> AgentResponse:
        """
        Review execution output for quality and correctness.
        
        Analyzes the output for errors, warnings, and completeness.
        Returns approval or rejection with feedback.
        
        Args:
            execution_output: Output text from ExecutorAgent
            
        Returns:
            AgentResponse with review decision and feedback
            
        Example:
            >>> reviewer = ReviewerAgent()
            >>> output = "Task completed successfully"
            >>> response = reviewer.review(output)
            >>> print(response.content)
        """
        if not execution_output or not execution_output.strip():
            return AgentResponse(
                content="Error: Empty output",
                metadata={
                    "agent_id": self.agent_id,
                    "status": "error",
                    "error": "Execution output cannot be empty"
                }
            )
        
        # Increment counter
        self.reviews_completed += 1
        
        # Perform review analysis
        issues = self._check_for_issues(execution_output)
        quality_score = self._calculate_quality_score(execution_output, issues)
        
        # Determine approval
        is_approved = len(issues) == 0 and quality_score >= 0.7
        
        if is_approved:
            self.approvals += 1
            status = "approved"
            decision = "✓ APPROVED"
            feedback = "Execution output meets quality standards."
        else:
            self.rejections += 1
            status = "rejected"
            decision = "✗ REJECTED"
            feedback = "Execution output requires revision."
        
        # Build review content
        review_lines = [
            "Review Results:",
            "=" * 50,
            f"Decision: {decision}",
            f"Quality Score: {quality_score:.2f}/1.00",
            ""
        ]
        
        if issues:
            review_lines.append("Issues Found:")
            for i, issue in enumerate(issues, 1):
                review_lines.append(f"  {i}. {issue['type']}: {issue['description']}")
            review_lines.append("")
        
        review_lines.append(f"Feedback: {feedback}")
        
        if not is_approved:
            review_lines.append("")
            review_lines.append("Recommended Actions:")
            for i, action in enumerate(self._get_recommended_actions(issues), 1):
                review_lines.append(f"  {i}. {action}")
        
        return AgentResponse(
            content="\n".join(review_lines),
            metadata={
                "agent_id": self.agent_id,
                "agent_type": "reviewer",
                "status": status,
                "approved": is_approved,
                "quality_score": quality_score,
                "issues_found": len(issues),
                "reviews_completed": self.reviews_completed,
                "approvals": self.approvals,
                "rejections": self.rejections,
                "issues": issues
            }
        )
    
    def _check_for_issues(self, output: str) -> List[Dict]:
        """
        Check output for common issues and errors.
        
        Args:
            output: Execution output text
            
        Returns:
            List of issue dictionaries
        """
        issues = []
        output_lower = output.lower()
        
        # Check for error keywords
        error_keywords = [
            "error", "exception", "failed", "failure",
            "traceback", "stack trace", "fatal"
        ]
        
        for keyword in error_keywords:
            if keyword in output_lower:
                issues.append({
                    "type": "error",
                    "severity": "high",
                    "description": f"Found error indicator: '{keyword}'"
                })
        
        # Check for warning indicators
        warning_keywords = ["warning", "warn", "caution", "deprecated"]
        
        for keyword in warning_keywords:
            if keyword in output_lower:
                issues.append({
                    "type": "warning",
                    "severity": "medium",
                    "description": f"Found warning indicator: '{keyword}'"
                })
        
        # Check for incomplete execution
        if "incomplete" in output_lower or "partial" in output_lower:
            issues.append({
                "type": "incomplete",
                "severity": "high",
                "description": "Execution appears incomplete"
            })
        
        # Check output length (very short might be incomplete)
        if len(output.strip()) < 50:
            issues.append({
                "type": "insufficient_output",
                "severity": "medium",
                "description": "Output is very short, may be incomplete"
            })
        
        return issues
    
    def _calculate_quality_score(self, output: str, issues: List[Dict]) -> float:
        """
        Calculate a quality score for the output.
        
        Args:
            output: Execution output text
            issues: List of detected issues
            
        Returns:
            Quality score between 0.0 and 1.0
        """
        score = 1.0
        
        # Deduct points for issues
        for issue in issues:
            if issue["severity"] == "high":
                score -= 0.3
            elif issue["severity"] == "medium":
                score -= 0.15
            else:
                score -= 0.05
        
        # Ensure score doesn't go below 0
        score = max(0.0, score)
        
        # Bonus for good indicators
        output_lower = output.lower()
        if "success" in output_lower or "completed" in output_lower:
            score += 0.1
        
        # Cap at 1.0
        score = min(1.0, score)
        
        return score
    
    def _get_recommended_actions(self, issues: List[Dict]) -> List[str]:
        """
        Generate recommended actions based on issues found.
        
        Args:
            issues: List of detected issues
            
        Returns:
            List of recommended action strings
        """
        actions = []
        
        issue_types = [issue["type"] for issue in issues]
        
        if "error" in issue_types:
            actions.append("Fix all errors before resubmitting")
            actions.append("Check error logs for detailed information")
        
        if "warning" in issue_types:
            actions.append("Address warnings to improve quality")
        
        if "incomplete" in issue_types or "insufficient_output" in issue_types:
            actions.append("Ensure all steps complete successfully")
            actions.append("Verify output contains expected information")
        
        if not actions:
            actions.append("Review output and resubmit")
        
        return actions
