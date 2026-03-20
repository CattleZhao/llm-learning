"""
Main entry point for the Multi-Agent Code Reviewer.

This module provides the CLI interface and orchestrates the agent execution.
"""

import os
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax

from langgraph.graph import StateGraph, END

# Add src directory to path for imports
src_dir = Path(__file__).parent
sys.path.insert(0, str(src_dir))

from utils.state import ReviewerState, create_initial_state, state_to_dict, CodeFinding
from utils.parser import read_file
from agents.code_analyzer import code_analyzer_node

# ============================================================================
# Configuration
# ============================================================================

console = Console()
app = typer.Typer(help="Multi-Agent Code Reviewer - LangGraph Implementation")


# ============================================================================
# Graph Construction
# ============================================================================

def create_review_graph() -> StateGraph:
    """
    Create the LangGraph StateGraph for code review.

    Currently implements a single agent (code_analyzer).
    More agents will be added in subsequent days.
    """
    # Create the graph with our state type
    graph = StateGraph(ReviewerState)

    # Add nodes (agents)
    graph.add_node("code_analyzer", code_analyzer_node)

    # Define the flow
    graph.set_entry_point("code_analyzer")
    graph.add_edge("code_analyzer", END)

    # Compile the graph
    return graph.compile()


# ============================================================================
# Output Formatting
# ============================================================================

def print_banner():
    """Print the application banner."""
    console.print(Panel(
        "[bold cyan]🤖 Multi-Agent Code Reviewer[/bold cyan]\n"
        "[dim]LangGraph Implementation - Day 1[/dim]",
        border_style="cyan"
    ))


def print_results(state: ReviewerState):
    """Print the analysis results in a formatted way."""
    console.print("\n[bold]─" * 60 + "[/bold]\n")

    # Print metrics
    metrics = state.get("code_metrics")
    if metrics:
        console.print("[bold yellow]📊 Code Metrics[/bold yellow]\n")

        table = Table(show_header=False, box=None)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Total Lines", str(metrics.total_lines))
        table.add_row("Code Lines", str(metrics.code_lines))
        table.add_row("Comment Lines", str(metrics.comment_lines))
        table.add_row("Blank Lines", str(metrics.blank_lines))
        table.add_row("Functions", str(metrics.num_functions))
        table.add_row("Classes", str(metrics.num_classes))
        table.add_row("Avg Complexity", f"{metrics.avg_complexity:.2f}")

        console.print(table)
        console.print()

    # Print findings
    findings = state.get("findings", [])
    if findings:
        console.print(f"[bold yellow]🔍 Findings ({len(findings)})[/bold yellow]\n")

        # Group by severity
        by_severity = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": [],
            "info": [],
        }

        for f in findings:
            by_severity[f.severity].append(f)

        # Print in order of severity
        severity_order = ["critical", "high", "medium", "low", "info"]
        severity_colors = {
            "critical": "red bold",
            "high": "red",
            "medium": "yellow",
            "low": "blue",
            "info": "dim",
        }

        for severity in severity_order:
            items = by_severity[severity]
            if items:
                color = severity_colors[severity]
                console.print(f"[{color}]{severity.upper()}[/{color}] [{len(items)}]")

                for f in items[:10]:  # Limit to 10 per category
                    console.print(f"  [{color}]●[/{color}] {f.message}")
                    if f.suggestion:
                        console.print(f"    [dim]💡 {f.suggestion}[/dim]")
                    if f.line > 0:
                        console.print(f"    [dim]📍 Line {f.line}[/dim]")

                if len(items) > 10:
                    console.print(f"  ... and {len(items) - 10} more")

                console.print()

    # Print errors if any
    errors = state.get("errors", [])
    if errors:
        console.print("[bold red]❌ Errors[/bold red]\n")
        for error in errors:
            console.print(f"  [red]• {error}[/red]")
        console.print()


# ============================================================================
# CLI Commands
# ============================================================================

@app.command()
def analyze(
    path: str = typer.Argument(..., help="Path to the Python file to analyze"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    show_code: bool = typer.Option(False, "--show-code", help="Show the code being analyzed"),
):
    """
    Analyze a Python file using the multi-agent code reviewer.

    Example:
        python src/main.py analyze examples/sample_code.py
    """
    print_banner()

    # Resolve path
    file_path = Path(path)
    if not file_path.exists():
        console.print(f"[red]Error: File not found: {path}[/red]")
        raise typer.Exit(1)

    if not file_path.suffix == ".py":
        console.print(f"[red]Error: Only Python files are supported[/red]")
        raise typer.Exit(1)

    # Read code
    try:
        code = read_file(str(file_path))
    except Exception as e:
        console.print(f"[red]Error reading file: {e}[/red]")
        raise typer.Exit(1)

    if show_code:
        console.print(Panel(
            Syntax(code, "python", line_numbers=True),
            title=f"[dim]{path}[/dim]",
            border_style="dim"
        ))

    # Create initial state
    console.print(f"[cyan]📄 Analyzing:[/cyan] {path}")
    console.print(f"[cyan]📏 Size:[/cyan] {len(code)} bytes\n")

    initial_state = create_initial_state(str(file_path), code)

    # Create and run the graph
    console.print("[dim]Initializing agent graph...[/dim]\n")

    try:
        graph = create_review_graph()
        result_state = graph.invoke(initial_state)
    except Exception as e:
        console.print(f"[red]Error during analysis: {e}[/red]")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        raise typer.Exit(1)

    # Print results
    print_results(result_state)

    console.print("[bold green]✅ Analysis complete![/bold green]\n")


@app.command()
def version():
    """Show version information."""
    console.print("[cyan]Multi-Agent Code Reviewer[/cyan] [dim]v0.1.0[/dim]")
    console.print("[dim]Day 1 Implementation - Single Agent[/dim]\n")


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    app()
