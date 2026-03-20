"""
Shared state definition for the multi-agent code reviewer.

This module defines the State schema that flows between all agents.
Each agent can read and modify specific fields in the state.
"""

from typing import TypedDict, Annotated, List, Dict, Any, Optional
from operator import add
from pydantic import BaseModel, Field


# ============================================================================
# Individual Finding Models
# ============================================================================

class CodeFinding(BaseModel):
    """A single code analysis finding."""

    agent: str = Field(description="Name of the agent that found this issue")
    category: str = Field(description="Category: structure|security|performance|style")
    severity: str = Field(description="Severity: critical|high|medium|low|info")
    line: int = Field(description="Line number where the issue occurs", default=0)
    file: str = Field(description="File path")
    message: str = Field(description="Description of the finding")
    suggestion: Optional[str] = Field(description="Suggested fix", default=None)


class CodeMetrics(BaseModel):
    """Code complexity metrics."""

    total_lines: int = 0
    code_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    num_functions: int = 0
    num_classes: int = 0
    avg_complexity: float = 0.0


# ============================================================================
# Main Agent State
# ============================================================================

class ReviewerState(TypedDict):
    """
    Shared state that flows between all agents in the graph.

    Field Behavior:
    - Plain fields get OVERWRITTEN when a node returns them
    - Annotated[..., add] fields ACCUMULATE when a node appends to them
    """

    # === Input fields (set once, never changed) ===
    target_path: str                    # Path to the code being analyzed
    code_content: str                   # Raw code content

    # === Accumulated findings (all agents contribute here) ===
    # Using Annotated with add operator makes these accumulate
    findings: Annotated[List[CodeFinding], add]

    # === Agent-specific results (each agent overwrites their field) ===
    code_metrics: Optional[CodeMetrics]          # From code_analyzer
    security_issues: List[Dict[str, Any]]        # From security_auditor
    performance_issues: List[Dict[str, Any]]     # From performance_optimizer
    style_issues: List[Dict[str, Any]]           # From style_checker

    # === Execution tracking ===
    agents_completed: Annotated[List[str], add]  # Track which agents have run
    current_agent: Optional[str]                 # Currently running agent
    errors: Annotated[List[str], add]            # Any errors that occurred

    # === Final output ===
    final_report: Optional[str]                  # Generated final report


# ============================================================================
# Helper Functions
# ============================================================================

def create_initial_state(target_path: str, code_content: str) -> ReviewerState:
    """Create the initial state for a new review run."""
    return {
        "target_path": target_path,
        "code_content": code_content,
        "findings": [],
        "code_metrics": None,
        "security_issues": [],
        "performance_issues": [],
        "style_issues": [],
        "agents_completed": [],
        "current_agent": None,
        "errors": [],
        "final_report": None,
    }


def state_to_dict(state: ReviewerState) -> Dict[str, Any]:
    """Convert state to a regular dict for serialization."""
    return {
        "target_path": state.get("target_path"),
        "findings": [f.model_dump() if hasattr(f, "model_dump") else f for f in state.get("findings", [])],
        "code_metrics": state.get("code_metrics").model_dump() if state.get("code_metrics") else None,
        "agents_completed": state.get("agents_completed", []),
        "errors": state.get("errors", []),
    }
