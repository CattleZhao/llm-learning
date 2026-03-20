"""
Code Analyzer Agent - Analyzes code structure and complexity.

This is the first agent in our multi-agent system.
It focuses on structural analysis of the code.
"""

import os
from typing import Dict, Any
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate

from utils.state import ReviewerState, CodeFinding
from utils.parser import (
    parse_code_structure,
    calculate_metrics,
    get_high_complexity_functions,
    find_duplicate_code,
)


# ============================================================================
# Agent Configuration
# ============================================================================

MODEL_NAME = os.getenv("MODEL_NAME", "claude-sonnet-4-6")

# Initialize the LLM
llm = ChatAnthropic(
    model=MODEL_NAME,
    temperature=0,
    max_tokens=4096,
)


# ============================================================================
# Analysis Prompts
# ============================================================================

ANALYSIS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a code analysis expert. Your task is to review the provided code structure information and identify issues.

Focus on:
1. Code organization and structure
2. Function complexity and design issues
3. Code duplication
4. Naming conventions
5. Missing documentation

For each issue, provide:
- Category: structure
- Severity: critical|high|medium|low|info
- Line number (if applicable)
- Clear description
- Specific suggestion for improvement

Respond in the following format for each issue:
ISSUE: <description>
SEVERITY: <severity>
LINE: <line number or N/A>
SUGGESTION: <specific suggestion>
---

"""),
    ("human", """Analyze the following code structure:

File: {file_path}

Metrics:
- Total lines: {total_lines}
- Code lines: {code_lines}
- Functions: {num_functions}
- Classes: {num_classes}
- Average complexity: {avg_complexity:.2f}

Functions:
{functions}

Classes:
{classes}

High complexity functions (complexity >= {complexity_threshold}):
{high_complexity}

Potential duplicates:
{duplicates}

Provide your analysis."""),
])


# ============================================================================
# Agent Node Function
# ============================================================================

def code_analyzer_node(state: ReviewerState) -> Dict[str, Any]:
    """
    The Code Analyzer agent node.

    This function:
    1. Parses the code structure
    2. Calculates metrics
    3. Identifies issues (complexity, duplication, etc.)
    4. Uses LLM to generate analysis
    5. Returns updated state with findings and metrics

    Args:
        state: Current reviewer state

    Returns:
        Dict with updates to state (metrics and findings)
    """
    print("🔍 [Code Analyzer] Starting analysis...")

    code_content = state.get("code_content", "")
    target_path = state.get("target_path", "")

    if not code_content:
        print("❌ [Code Analyzer] No code content found")
        return {
            "current_agent": None,
            "errors": ["Code Analyzer: No code content to analyze"]
        }

    findings = []

    # ========================================================================
    # Step 1: Static Analysis (without LLM)
    # ========================================================================

    print("  → Calculating metrics...")
    metrics = calculate_metrics(code_content)
    print(f"     Lines: {metrics.total_lines}, Functions: {metrics.num_functions}, Classes: {metrics.num_classes}")

    # Parse structure
    print("  → Parsing code structure...")
    structure = parse_code_structure(code_content)

    # Find high complexity functions
    high_complexity = get_high_complexity_functions(code_content, threshold=10)
    if high_complexity:
        print(f"  ⚠️  Found {len(high_complexity)} high complexity functions")
        for func in high_complexity:
            findings.append(CodeFinding(
                agent="code_analyzer",
                category="structure",
                severity="high" if func["complexity"] >= 15 else "medium",
                line=func["lineno"],
                file=target_path,
                message=f"Function '{func['name']}' has high cyclomatic complexity: {func['complexity']}",
                suggestion="Consider breaking this function into smaller functions or simplifying the logic."
            ))

    # Find duplicates
    print("  → Checking for code duplication...")
    duplicates = find_duplicate_code(code_content, min_lines=5)
    if duplicates:
        print(f"  ⚠️  Found {len(duplicates)} potential duplicate blocks")
        # Add a summary finding for duplicates
        findings.append(CodeFinding(
            agent="code_analyzer",
            category="structure",
            severity="low",
            line=0,
            file=target_path,
            message=f"Found {len(duplicates)} potentially duplicated code blocks",
            suggestion="Consider extracting common code into reusable functions."
        ))

    # Check for missing docstrings
    print("  → Checking documentation...")
    functions_without_docstring = [
        f for f in structure.get("functions", [])
        if not f.get("docstring")
    ]
    if functions_without_docstring:
        print(f"  ⚠️  {len(functions_without_docstring)} functions lack docstrings")
        # Add a summary finding
        if len(functions_without_docstring) > 3:
            findings.append(CodeFinding(
                agent="code_analyzer",
                category="structure",
                severity="info",
                line=0,
                file=target_path,
                message=f"{len(functions_without_docstring)} functions are missing docstrings",
                suggestion="Add docstrings to improve code documentation."
            ))

    # ========================================================================
    # Step 2: LLM-Powered Analysis (for deeper insights)
    # ========================================================================

    print("  → Running LLM analysis...")

    # Format functions for the prompt
    functions_text = ""
    for func in structure.get("functions", [])[:10]:  # Limit to first 10
        functions_text += f"  - {func['name']} (line {func['lineno']})\n"

    # Format classes
    classes_text = ""
    for cls in structure.get("classes", [])[:5]:
        classes_text += f"  - {cls['name']} (line {cls['lineno']})\n"
        for method in cls.get("methods", [])[:5]:
            classes_text += f"    - {method['name']}()\n"

    # Format high complexity
    high_complexity_text = ""
    for func in high_complexity[:5]:
        high_complexity_text += f"  - {func['name']}: {func['complexity']} (line {func['lineno']})\n"

    # Format duplicates
    duplicates_text = ""
    for dup in duplicates[:3]:
        duplicates_text += f"  - Lines {dup['start_line_1']} and {dup['start_line_2']}\n"

    # Invoke LLM
    try:
        response = ANALYSIS_PROMPT.format(
            file_path=target_path,
            total_lines=metrics.total_lines,
            code_lines=metrics.code_lines,
            num_functions=metrics.num_functions,
            num_classes=metrics.num_classes,
            avg_complexity=metrics.avg_complexity,
            functions=functions_text or "  None",
            classes=classes_text or "  None",
            complexity_threshold=10,
            high_complexity=high_complexity_text or "  None",
            duplicates=duplicates_text or "  None",
        )

        result = llm.invoke(response)
        llm_findings = _parse_llm_response(result.content, target_path)
        findings.extend(llm_findings)

    except Exception as e:
        print(f"  ⚠️  LLM analysis failed: {e}")

    # ========================================================================
    # Step 3: Return updated state
    # ========================================================================

    print(f"✅ [Code Analyzer] Complete. Found {len(findings)} issues.\n")

    return {
        "code_metrics": metrics,
        "findings": findings,
        "agents_completed": ["code_analyzer"],
        "current_agent": None,
    }


# ============================================================================
# Helper Functions
# ============================================================================

def _parse_llm_response(response: str, file_path: str) -> list:
    """
    Parse the LLM response and extract CodeFinding objects.

    Expected format:
    ISSUE: <description>
    SEVERITY: <severity>
    LINE: <line number or N/A>
    SUGGESTION: <suggestion>
    ---
    """
    findings = []
    blocks = response.split("---")

    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 3:
            continue

        issue = severity = line_num = suggestion = None

        for line in lines:
            if line.startswith("ISSUE:"):
                issue = line.split(":", 1)[1].strip()
            elif line.startswith("SEVERITY:"):
                severity = line.split(":", 1)[1].strip().lower()
            elif line.startswith("LINE:"):
                line_str = line.split(":", 1)[1].strip()
                line_num = int(line_str) if line_str.isdigit() else 0
            elif line.startswith("SUGGESTION:"):
                suggestion = line.split(":", 1)[1].strip()

        if issue and severity:
            findings.append(CodeFinding(
                agent="code_analyzer",
                category="structure",
                severity=severity if severity in ["critical", "high", "medium", "low", "info"] else "info",
                line=line_num or 0,
                file=file_path,
                message=issue,
                suggestion=suggestion,
            ))

    return findings


# ============================================================================
# Standalone Test Function
# ============================================================================

if __name__ == "__main__":
    # Test the agent directly
    from ..utils.state import create_initial_state
    from ..utils.parser import read_file

    test_file = "../examples/sample_code.py"
    code = read_file(test_file)

    state = create_initial_state(test_file, code)
    result = code_analyzer_node(state)

    print("\n=== Results ===")
    print(f"Metrics: {result['code_metrics']}")
    print(f"\nFindings ({len(result['findings'])}):")
    for finding in result['findings']:
        print(f"  [{finding.severity.upper()}] {finding.message}")
