"""
CLI Interface for Project 4 CrewAI

使用 Typer 提供命令行接口。

注意：此模块需要安装 typer 和 rich。请运行：
    pip install typer rich
"""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from src.crews.code_crew import CodeDevelopmentCrew

# Create CLI app
app = typer.Typer(help="Project 4 CrewAI - AI-Powered Code Development Crew")
console = Console()


@app.command()
def run(
    task: str = typer.Option(
        ...,
        "--task",
        "-t",
        help="Task description for the crew to execute",
        prompt="Enter task description"
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        "-d",
        help="Enable debug mode for verbose output"
    )
):
    """
    Run the Code Development Crew with a specified task.

    This command orchestrates the complete development workflow:
    - Coordinator manages the process
    - Coder implements the solution
    - Reviewer checks code quality
    - Tester validates the implementation
    - Coordinator aggregates final results
    """
    # Display welcome banner
    console.print(Panel.fit(
        Text("Project 4 CrewAI", style="bold blue"),
        subtitle="AI-Powered Code Development"
    ))

    # Display task information
    console.print(f"\n[bold]Task:[/bold] {task}")
    if debug:
        console.print("[yellow]Debug mode: ENABLED[/yellow]")

    try:
        # Create and run the crew
        console.print("\n[cyan]Initializing crew...[/cyan]")
        crew = CodeDevelopmentCrew()

        console.print("[cyan]Executing workflow...[/cyan]")
        console.print("[dim]This may take a few minutes...[/dim]\n")

        result = crew.kickoff(task)

        # Display results
        console.print("\n[green]✓[/green] [bold green]Task completed successfully![/bold green]")
        console.print(Panel(
            str(result),
            title="[bold]Execution Results[/bold]",
            border_style="green"
        ))

    except ImportError as e:
        console.print(f"\n[red]Error:[/red] {str(e)}")
        raise typer.Exit(code=1)

    except Exception as e:
        console.print(f"\n[red]Error executing task:[/red] {str(e)}")
        if debug:
            import traceback
            console.print(traceback.format_exc())
        raise typer.Exit(code=1)


@app.command()
def version():
    """Display version information."""
    console.print("[bold blue]Project 4 CrewAI[/bold blue]")
    console.print("Version: 1.0.0")
    console.print("\n[bold]Components:[/bold]")
    console.print("  - CrewAI: AI agent orchestration")
    console.print("  - Typer: CLI framework")
    console.print("  - Rich: Terminal formatting")


@app.callback()
def main(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output"
    )
):
    """
    Project 4 CrewAI - AI-Powered Code Development Crew

    An intelligent code development system using multiple AI agents:
    - Coordinator: Project management
    - Coder: Code implementation
    - Reviewer: Code quality assurance
    - Tester: Test coverage and validation
    """
    if verbose:
        console.print("[yellow]Verbose mode enabled[/yellow]")


if __name__ == "__main__":
    app()
