"""代码分析工具模块 - 使用AST解析Python代码"""

import ast
from typing import Dict, List, Any
from functools import wraps


def tool(func):
    """装饰器，标记方法可被Agent调用"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        return {
            "tool": func.__name__,
            "result": result
        }
    wrapper._raw = func  # 保存原始未装饰的方法
    return wrapper


class CodeAnalyzer:
    """Python代码分析器，使用AST进行静态代码分析"""

    def __init__(self, source_code: str = None, file_path: str = None):
        """
        初始化代码分析器

        Args:
            source_code: Python源代码字符串
            file_path: Python文件路径
        """
        if source_code:
            self.source_code = source_code
        elif file_path:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.source_code = f.read()
        else:
            raise ValueError("必须提供source_code或file_path")

        try:
            self.tree = ast.parse(self.source_code)
        except SyntaxError as e:
            raise ValueError(f"代码解析失败: {e}")

        self.lines = self.source_code.split('\n')

    @tool
    def analyze_functions(self) -> List[Dict[str, Any]]:
        """
        分析代码中的所有函数

        Returns:
            函数信息列表，每个函数包含：
            - name: 函数名
            - args_count: 参数数量
            - line_number: 起始行号
            - is_method: 是否为类方法
        """
        functions = []

        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                # 计算参数数量
                args_count = len(node.args.args)
                # 排除self参数
                if args_count > 0 and node.args.args[0].arg == 'self':
                    is_method = True
                else:
                    is_method = False

                functions.append({
                    'name': node.name,
                    'args_count': args_count,
                    'line_number': node.lineno,
                    'is_method': is_method
                })

        return functions

    @tool
    def count_lines(self) -> Dict[str, int]:
        """
        统计代码行数

        Returns:
            包含以下字段的字典：
            - total: 总行数
            - non_empty: 非空行数
            - comments: 注释行数
            - code: 代码行数（非空且非注释）
        """
        total = len(self.lines)
        non_empty = 0
        comments = 0
        code = 0

        in_multiline_string = False
        multiline_delim = None

        for line in self.lines:
            stripped = line.strip()

            # 处理多行字符串
            if '"""' in stripped or "'''" in stripped:
                if not in_multiline_string:
                    in_multiline_string = True
                    if '"""' in stripped:
                        multiline_delim = '"""'
                    else:
                        multiline_delim = "'''"
                    # 单行内的多行字符串
                    if stripped.count(multiline_delim) >= 2:
                        in_multiline_string = False
                else:
                    if multiline_delim in stripped:
                        in_multiline_string = False

            # 跳过多行字符串内部
            if in_multiline_string:
                continue

            # 跳过空行
            if not stripped:
                continue

            non_empty += 1

            # 检查是否为注释
            if stripped.startswith('#'):
                comments += 1
            else:
                code += 1

        return {
            'total': total,
            'non_empty': non_empty,
            'comments': comments,
            'code': code
        }

    @tool
    def get_imports(self) -> Dict[str, List[str]]:
        """
        获取所有import语句

        Returns:
            包含以下字段的字典：
            - standard_imports: 标准import语句
            - from_imports: from ... import ... 语句
        """
        standard_imports = []
        from_imports = []

        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    standard_imports.append({
                        'module': alias.name,
                        'alias': alias.asname,
                        'line_number': node.lineno
                    })
            elif isinstance(node, ast.ImportFrom):
                module_name = node.module if node.module else ''
                imports = []
                for alias in node.names:
                    imports.append({
                        'name': alias.name,
                        'alias': alias.asname
                    })
                from_imports.append({
                    'module': module_name,
                    'imports': imports,
                    'line_number': node.lineno
                })

        return {
            'standard_imports': standard_imports,
            'from_imports': from_imports
        }

    @tool
    def analyze_classes(self) -> List[Dict[str, Any]]:
        """
        分析代码中的所有类

        Returns:
            类信息列表，每个类包含：
            - name: 类名
            - line_number: 起始行号
            - methods_count: 方法数量
            - base_classes: 基类列表
        """
        classes = []

        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef):
                # 获取基类
                base_classes = []
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        base_classes.append(base.id)
                    elif isinstance(base, ast.Attribute):
                        base_classes.append(ast.unparse(base))

                # 统计方法数量
                methods_count = 0
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        methods_count += 1

                classes.append({
                    'name': node.name,
                    'line_number': node.lineno,
                    'methods_count': methods_count,
                    'base_classes': base_classes
                })

        return classes

    @tool
    def get_complexity(self) -> Dict[str, Any]:
        """
        计算圈复杂度（简化版）

        Returns:
            包含复杂度信息的字典
        """
        complexity = 1  # 基础复杂度

        for node in ast.walk(self.tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.With)):
                complexity += 1
            elif isinstance(node, ast.Try):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1

        return {
            'cyclomatic_complexity': complexity,
            'level': self._get_complexity_level(complexity)
        }

    def _get_complexity_level(self, complexity: int) -> str:
        """根据复杂度值返回等级描述"""
        if complexity <= 5:
            return "low"
        elif complexity <= 10:
            return "moderate"
        elif complexity <= 20:
            return "high"
        else:
            return "very_high"

    @tool
    def get_full_report(self) -> Dict[str, Any]:
        """
        获取完整的代码分析报告

        Returns:
            包含所有分析结果的完整报告
        """
        # 使用原始未装饰的方法获取结果
        return {
            'functions': self.analyze_functions._raw(self),
            'classes': self.analyze_classes._raw(self),
            'lines': self.count_lines._raw(self),
            'imports': self.get_imports._raw(self),
            'complexity': self.get_complexity._raw(self)
        }
