"""
LangChain Tool 包装层

将原项目的工具函数包装为 LangChain Tool
"""
from langchain.tools import tool
from .code_analyzer import CodeAnalyzer
from typing import Dict, List, Any


@tool
def analyze_code(file_path: str) -> Dict[str, Any]:
    """
    分析Python代码文件，获取完整的代码结构报告。

    Args:
        file_path: Python文件的路径

    Returns:
        包含functions, classes, lines, imports, complexity的完整报告字典
    """
    try:
        analyzer = CodeAnalyzer(file_path=file_path)
        return analyzer.get_full_report()
    except Exception as e:
        return {"error": str(e)}


@tool
def list_functions(file_path: str) -> List[Dict[str, Any]]:
    """
    列出代码文件中的所有函数。

    Args:
        file_path: Python文件的路径

    Returns:
        函数信息列表，每个函数包含 name, args_count, line_number, is_method
    """
    try:
        analyzer = CodeAnalyzer(file_path=file_path)
        return analyzer.analyze_functions()
    except Exception as e:
        return [{"error": str(e)}]


@tool
def list_classes(file_path: str) -> List[Dict[str, Any]]:
    """
    列出代码文件中的所有类。

    Args:
        file_path: Python文件的路径

    Returns:
        类信息列表，每个类包含 name, line_number, methods_count, base_classes
    """
    try:
        analyzer = CodeAnalyzer(file_path=file_path)
        return analyzer.analyze_classes()
    except Exception as e:
        return [{"error": str(e)}]


@tool
def count_lines(file_path: str) -> Dict[str, int]:
    """
    统计代码文件的行数（总行数、代码行、注释行等）。

    Args:
        file_path: Python文件的路径

    Returns:
        包含 total, non_empty, comments, code 的统计字典
    """
    try:
        analyzer = CodeAnalyzer(file_path=file_path)
        return analyzer.count_lines()
    except Exception as e:
        return {"error": str(e)}


@tool
def get_imports(file_path: str) -> Dict[str, List[Dict]]:
    """
    获取代码文件中的所有import语句。

    Args:
        file_path: Python文件的路径

    Returns:
        包含 standard_imports 和 from_imports 的字典
    """
    try:
        analyzer = CodeAnalyzer(file_path=file_path)
        return analyzer.get_imports()
    except Exception as e:
        return {"error": str(e), "standard_imports": [], "from_imports": []}


@tool
def get_complexity(file_path: str) -> Dict[str, Any]:
    """
    计算代码的圈复杂度。

    Args:
        file_path: Python文件的路径

    Returns:
        包含 cyclomatic_complexity 和 level 的字典
    """
    try:
        analyzer = CodeAnalyzer(file_path=file_path)
        return analyzer.get_complexity()
    except Exception as e:
        return {"error": str(e), "cyclomatic_complexity": 0, "level": "unknown"}


@tool
def read_file(file_path: str) -> str:
    """
    读取文件内容。

    Args:
        file_path: 文件的路径

    Returns:
        文件内容字符串
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # 限制长度避免 token 溢出
        if len(content) > 5000:
            content = content[:5000] + "\n... (内容过长，已截断)"
        return content
    except Exception as e:
        return f"读取文件失败: {str(e)}"


def get_all_tools() -> List:
    """
    获取所有 LangChain 工具

    Returns:
        LangChain Tool 列表
    """
    return [
        analyze_code,
        list_functions,
        list_classes,
        count_lines,
        get_imports,
        get_complexity,
        read_file,
    ]
