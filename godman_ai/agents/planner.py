"""
Planner Agent - Decomposes user requests into actionable steps.

The PlannerAgent takes a user request and generates a structured plan
with discrete steps that can be executed by the ExecutorAgent.
"""

from dataclasses import dataclass, field
from typing import Dict, List


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


class PlannerAgent:
    """
    Planner agent that breaks down user requests into actionable steps.
    
    The planner analyzes the user's intent and creates a structured plan
    with numbered steps that guide execution.
    """
    
    def __init__(self, agent_id: str = "planner-001"):
        """
        Initialize the PlannerAgent.
        
        Args:
            agent_id: Unique identifier for this agent instance
        """
        self.agent_id = agent_id
        self.plans_created = 0
    
    def plan(self, user_request: str) -> AgentResponse:
        """
        Generate an execution plan from a user request.
        
        Args:
            user_request: Natural language request from the user
            
        Returns:
            AgentResponse containing the structured plan and metadata
            
        Example:
            >>> planner = PlannerAgent()
            >>> response = planner.plan("Analyze my receipts for tax deductions")
            >>> print(response.content)
        """
        if not user_request or not user_request.strip():
            return AgentResponse(
                content="Error: Empty request",
                metadata={
                    "agent_id": self.agent_id,
                    "status": "error",
                    "error": "User request cannot be empty"
                }
            )
        
        # Increment counter
        self.plans_created += 1
        
        # Mock plan generation - in production, this would use LLM
        steps = self._generate_mock_plan(user_request)
        
        plan_content = "\n".join(f"{i}. {step}" for i, step in enumerate(steps, 1))
        
        return AgentResponse(
            content=plan_content,
            metadata={
                "agent_id": self.agent_id,
                "agent_type": "planner",
                "status": "success",
                "user_request": user_request,
                "step_count": len(steps),
                "plans_created": self.plans_created
            }
        )
    
    def _generate_mock_plan(self, user_request: str) -> List[str]:
        """
        Generate a mock plan based on keywords in the request.
        
        This is a placeholder implementation. In production, this would
        be replaced with LLM-based plan generation.
        
        Args:
            user_request: The user's request
            
        Returns:
            List of plan steps
        """
        request_lower = user_request.lower()
        
        # Keyword-based plan generation
        if "receipt" in request_lower or "expense" in request_lower:
            return [
                "Load receipt data from CSV file",
                "Parse and validate receipt records",
                "Categorize expenses for tax purposes",
                "Generate summary report with totals",
                "Export results to output format"
            ]
        elif "analyze" in request_lower or "report" in request_lower:
            return [
                "Gather required data sources",
                "Perform data analysis",
                "Generate insights and findings",
                "Create formatted report",
                "Save results"
            ]
        elif "search" in request_lower or "find" in request_lower:
            return [
                "Parse search query",
                "Query relevant data sources",
                "Filter and rank results",
                "Format search results",
                "Return top matches"
            ]
        else:
            # Generic plan
            return [
                "Understand user request and context",
                "Identify required resources and data",
                "Execute primary task logic",
                "Validate and verify results",
                "Format and return response"
            ]
