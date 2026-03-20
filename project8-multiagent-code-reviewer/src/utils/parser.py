"""
Code parsing utilities for the multi-agent code reviewer.

This module provides functions to parse Python code and extract
structural information like functions, classes, and complexity metrics.
"""

import ast
import radon.complexity as radon_cc
import radon.metrics as radon_metrics
from typing import List, Dict, Any, Optional
from pathlib import Path

from .state import CodeMetrics


def read_file(file_path: str) -> str:
    """Read the content of a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise ValueError(f"File not found: {file_path}")
    except Exception as e:
        raise ValueError(f"Error reading file: {e}")


def parse_code_structure(code: str) -> Dict[str, Any]:
    """
    Parse Python code and extract structural information.

    Returns:
        Dict with keys: functions, classes, imports, globals
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return {
            "error": f"Syntax error at line {e.lineno}: {e.msg}",
            "functions": [],
            "classes": [],
            "imports": [],
        }

    functions = []
    classes = []
    imports = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            functions.append({
                "name": node.name,
                "lineno": node.lineno,
                "args": [arg.arg for arg in node.args.args],
                "docstring": ast.get_docstring(node),
                "decorator_list": [ast.unparse(d) for d in node.decorator_list],
            })
        elif isinstance(node, ast.ClassDef):
            methods = []
            bases = [ast.unparse(base) for base in node.bases]

            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    methods.append({
                        "name": item.name,
                        "lineno": item.lineno,
                        "args": [arg.arg for arg in item.args.args],
                    })

            classes.append({
                "name": node.name,
                "lineno": node.lineno,
                "bases": bases,
                "methods": methods,
                "docstring": ast.get_docstring(node),
            })
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                imports.append({
                    "name": alias.name,
                    "alias": alias.asname,
                })

    return {
        "functions": functions,
        "classes": classes,
        "imports": imports,
    }


def calculate_complexity(code: str) -> float:
    """
    Calculate the average cyclomatic complexity of the code.

    Uses radon library to compute complexity.
    """
    try:
        results = radon_cc.cc_visit(code)
        if not results:
            return 0.0

        total_complexity = sum(block.complexity for block in results)
        return total_complexity / len(results)
    except Exception:
        return 0.0


def calculate_metrics(code: str) -> CodeMetrics:
    """
    Calculate various code metrics.

    Returns a CodeMetrics object with:
    - Line counts (total, code, comment, blank)
    - Function and class counts
    - Average complexity
    """
    lines = code.split('\n')

    total_lines = len(lines)
    blank_lines = sum(1 for line in lines if not line.strip())
    comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
    code_lines = total_lines - blank_lines - comment_lines

    structure = parse_code_structure(code)
    num_functions = len(structure.get("functions", []))
    num_classes = len(structure.get("classes", []))

    avg_complexity = calculate_complexity(code)

    return CodeMetrics(
        total_lines=total_lines,
        code_lines=code_lines,
        comment_lines=comment_lines,
        blank_lines=blank_lines,
        num_functions=num_functions,
        num_classes=num_classes,
        avg_complexity=avg_complexity,
    )


def extract_function_code(code: str, function_name: str) -> Optional[str]:
    """Extract the source code of a specific function."""
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == function_name:
                return ast.get_source_segment(code, node)
    except Exception:
        pass
    return None


def get_high_complexity_functions(code: str, threshold: int = 10) -> List[Dict[str, Any]]:
    """
    Find functions with high cyclomatic complexity.

    Args:
        code: The source code to analyze
        threshold: Complexity threshold (default: 10)

    Returns:
        List of dicts with function info and complexity score
    """
    try:
        results = radon_cc.cc_visit(code)
        high_complexity = []

        for block in results:
            if block.complexity >= threshold:
                high_complexity.append({
                    "name": block.name,
                    "lineno": block.lineno,
                    "complexity": block.complexity,
                    "classname": block.classname,
                })

        return sorted(high_complexity, key=lambda x: x["complexity"], reverse=True)
    except Exception:
        return []


def find_duplicate_code(code: str, min_lines: int = 5) -> List[Dict[str, Any]]:
    """
    Find potentially duplicated code blocks.

    This is a simple heuristic-based implementation.
    For production, consider using tools like PMD-CPD or JPlag.
    """
    lines = code.split('\n')
    duplicates = []

    # Simple approach: look for repeated sequences
    for i in range(len(lines) - min_lines):
        sequence = '\n'.join(lines[i:i + min_lines])

        for j in range(i + min_lines, len(lines) - min_lines):
            compare = '\n'.join(lines[j:j + min_lines])

            if sequence == compare and sequence.strip():
                duplicates.append({
                    "start_line_1": i + 1,
                    "start_line_2": j + 1,
                    "length": min_lines,
                    "snippet": sequence[:50] + "..." if len(sequence) > 50 else sequence,
                })

    return duplicates
