"""测试生成工具模块 - 使用LLM生成pytest测试代码"""

import ast
import os
import re
import sys
from typing import Dict, List, Any, Optional
from functools import wraps

# 添加project1路径以导入GLM客户端
project1_path = os.path.join(os.path.dirname(__file__), '../../..', 'project1-basic-api', 'src')
if project1_path not in sys.path:
    sys.path.insert(0, project1_path)

try:
    from llm_client import GLMClient
except ImportError:
    # 如果无法导入，使用备用路径
    GLMClient = None


def tool(func):
    """装饰器，标记方法可被Agent调用"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        return {
            "tool": func.__name__,
            "result": result
        }
    return wrapper


class TestGenerator:
    """测试代码生成器，使用LLM生成pytest单元测试"""

    def __init__(self, source_code: str = None, file_path: str = None, llm_client=None):
        """
        初始化测试生成器

        Args:
            source_code: Python源代码字符串
            file_path: Python文件路径
            llm_client: LLM客户端实例（如果为None，则使用默认GLMClient）
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

        # 初始化LLM客户端
        if llm_client:
            self.llm_client = llm_client
        elif GLMClient is not None:
            try:
                self.llm_client = GLMClient()
            except Exception:
                self.llm_client = None
        else:
            self.llm_client = None

        self.file_path = file_path
        self._function_cache = None
        self._class_cache = None

    def _get_functions(self) -> List[Dict[str, Any]]:
        """获取代码中的所有函数信息"""
        if self._function_cache is not None:
            return self._function_cache

        functions = []
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                # 获取函数文档字符串
                docstring = ast.get_docstring(node)

                # 获取参数列表
                args_info = []
                for arg in node.args.args:
                    args_info.append({
                        'name': arg.arg,
                        'annotation': ast.unparse(arg.annotation) if arg.annotation else None
                    })

                # 获取返回类型注解
                return_annotation = ast.unparse(node.returns) if node.returns else None

                # 检查是否有返回值
                has_return = self._has_return_value(node)

                functions.append({
                    'name': node.name,
                    'args': args_info,
                    'docstring': docstring,
                    'return_annotation': return_annotation,
                    'has_return': has_return,
                    'lineno': node.lineno,
                    'is_method': self._is_method(node)
                })

        self._function_cache = functions
        return functions

    def _is_method(self, node) -> bool:
        """检查函数是否为类方法"""
        # 检查父节点是否为ClassDef
        for parent in ast.walk(self.tree):
            if isinstance(parent, ast.ClassDef):
                for item in parent.body:
                    if item is node:
                        return True
        return False

    def _has_return_value(self, node) -> bool:
        """检查函数是否有返回值"""
        for child in ast.walk(node):
            if isinstance(child, ast.Return) and child.value is not None:
                return True
        return False

    def _get_classes(self) -> List[Dict[str, Any]]:
        """获取代码中的所有类信息"""
        if self._class_cache is not None:
            return self._class_cache

        classes = []
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef):
                docstring = ast.get_docstring(node)
                methods = []

                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        methods.append(item.name)

                classes.append({
                    'name': node.name,
                    'docstring': docstring,
                    'methods': methods,
                    'lineno': node.lineno
                })

        self._class_cache = classes
        return classes

    def _build_test_generation_prompt(self, function_name: str, function_info: Dict) -> str:
        """构建测试代码生成的提示词"""
        args_desc = ", ".join([arg['name'] for arg in function_info['args']])

        prompt = f"""你是一个专业的Python测试工程师。请为以下函数生成完整的pytest单元测试代码。

函数信息：
- 函数名: {function_name}
- 参数: {args_desc}
- 返回类型: {function_info.get('return_annotation', 'Unknown')}
- 文档字符串: {function_info.get('docstring', '无')}

函数源代码：
```python
{self._get_function_source(function_name)}
```

要求：
1. 使用pytest框架
2. 包含正常场景的测试用例
3. 包含异常场景的测试用例（如果适用）
4. 使用pytest.mark.parametrize进行参数化测试（如果适用）
5. 添加清晰的测试描述
6. 使用pytest的断言方法（如assert、pytest.raises等）
7. 测试函数名以test_开头

请只返回测试代码，不要包含任何解释说明。"""

        return prompt

    def _get_function_source(self, function_name: str) -> str:
        """获取函数的源代码"""
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef) and node.name == function_name:
                return ast.unparse(node)
        return ""

    def _extract_code_from_response(self, response: str) -> str:
        """从LLM响应中提取代码块"""
        # 尝试提取markdown代码块
        code_block_pattern = r'```python\n(.*?)```'
        matches = re.findall(code_block_pattern, response, re.DOTALL)
        if matches:
            return matches[0].strip()

        # 尝试提取普通代码块
        code_block_pattern = r'```\n(.*?)```'
        matches = re.findall(code_block_pattern, response, re.DOTALL)
        if matches:
            return matches[0].strip()

        # 如果没有代码块，返回整个响应
        return response.strip()

    @tool
    def generate_test(self, function_name: str) -> Dict[str, Any]:
        """
        为指定函数生成单元测试代码

        Args:
            function_name: 要生成测试的函数名

        Returns:
            包含以下字段的字典：
            - function_name: 函数名
            - test_code: 生成的测试代码
            - test_cases: 测试用例列表
            - success: 是否成功生成
        """
        functions = self._get_functions()
        target_func = None

        for func in functions:
            if func['name'] == function_name:
                target_func = func
                break

        if not target_func:
            return {
                'function_name': function_name,
                'test_code': None,
                'test_cases': [],
                'success': False,
                'error': f'未找到函数: {function_name}'
            }

        # 如果有LLM客户端，使用LLM生成测试
        if self.llm_client:
            try:
                prompt = self._build_test_generation_prompt(function_name, target_func)
                response = self.llm_client.generate(
                    prompt=prompt,
                    temperature=0.3,  # 使用较低的温度以获得更确定的输出
                    max_tokens=2000
                )
                test_code = self._extract_code_from_response(response)
            except Exception as e:
                # 如果LLM调用失败，回退到模板生成
                test_code = self._generate_test_template(function_name, target_func)
        else:
            # 没有LLM客户端时，使用模板生成
            test_code = self._generate_test_template(function_name, target_func)

        # 提取测试用例
        test_cases = self._extract_test_cases(test_code)

        return {
            'function_name': function_name,
            'test_code': test_code,
            'test_cases': test_cases,
            'success': True
        }

    def _generate_test_template(self, function_name: str, function_info: Dict) -> str:
        """生成测试代码模板（当LLM不可用时使用）"""
        args_list = [arg['name'] for arg in function_info['args']]
        args_str = ", ".join(args_list)

        test_code = f'''import pytest


class Test{function_name.capitalize()}:
    """{function_name}函数的测试类"""

    def test_{function_name}_basic(self):
        """测试{function_name}的基本功能"""
        # TODO: 添加测试逻辑
        # 函数签名: {function_name}({args_str})
        result = {function_name}(
            # TODO: 添加实际参数
        )
        # TODO: 添加断言
        assert result is not None

    def test_{function_name}_edge_cases(self):
        """测试{function_name}的边界情况"""
        # TODO: 添加边界测试
        pass

    def test_{function_name}_error_handling(self):
        """测试{function_name}的错误处理"""
        # TODO: 添加异常测试
        pass
'''

        return test_code

    def _extract_test_cases(self, test_code: str) -> List[str]:
        """从测试代码中提取测试用例名称"""
        test_cases = []
        # 匹配 test_xxx 函数名
        pattern = r'def (test_[a-zA-Z_][a-zA-Z0-9_]*)\('
        matches = re.findall(pattern, test_code)
        test_cases.extend(matches)
        return test_cases

    @tool
    def generate_edge_cases(self, function_name: str) -> Dict[str, Any]:
        """
        为指定函数生成边界测试场景

        Args:
            function_name: 要生成边界测试的函数名

        Returns:
            包含以下字段的字典：
            - function_name: 函数名
            - edge_cases: 边界测试场景列表
            - test_code: 边界测试代码
        """
        functions = self._get_functions()
        target_func = None

        for func in functions:
            if func['name'] == function_name:
                target_func = func
                break

        if not target_func:
            return {
                'function_name': function_name,
                'edge_cases': [],
                'test_code': None,
                'error': f'未找到函数: {function_name}'
            }

        # 分析参数类型，生成边界场景
        edge_cases = self._analyze_edge_cases(target_func)

        # 生成边界测试代码
        test_code = self._generate_edge_case_test_code(function_name, edge_cases)

        return {
            'function_name': function_name,
            'edge_cases': edge_cases,
            'test_code': test_code
        }

    def _analyze_edge_cases(self, function_info: Dict) -> List[Dict[str, Any]]:
        """分析函数参数，生成边界测试场景"""
        edge_cases = []

        for arg in function_info['args']:
            arg_name = arg['name']
            arg_type = arg.get('annotation')

            # 基于参数类型生成边界场景
            if arg_type in ('int', 'Optional[int]', 'int | None'):
                edge_cases.extend([
                    {
                        'param': arg_name,
                        'scenario': 'zero',
                        'value': 0,
                        'description': f'{arg_name}为零'
                    },
                    {
                        'param': arg_name,
                        'scenario': 'negative',
                        'value': -1,
                        'description': f'{arg_name}为负数'
                    },
                    {
                        'param': arg_name,
                        'scenario': 'max_int',
                        'value': 2**31 - 1,
                        'description': f'{arg_name}为最大整数值'
                    }
                ])
            elif arg_type in ('str', 'Optional[str]', 'str | None'):
                edge_cases.extend([
                    {
                        'param': arg_name,
                        'scenario': 'empty_string',
                        'value': '""',
                        'description': f'{arg_name}为空字符串'
                    },
                    {
                        'param': arg_name,
                        'scenario': 'none',
                        'value': 'None',
                        'description': f'{arg_name}为None'
                    }
                ])
            elif arg_type in ('list', 'List', 'Optional[list]', 'list | None'):
                edge_cases.extend([
                    {
                        'param': arg_name,
                        'scenario': 'empty_list',
                        'value': '[]',
                        'description': f'{arg_name}为空列表'
                    },
                    {
                        'param': arg_name,
                        'scenario': 'single_element',
                        'value': '[item]',
                        'description': f'{arg_name}只有一个元素'
                    }
                ])
            elif arg_type in ('dict', 'Dict', 'Optional[dict]', 'dict | None'):
                edge_cases.extend([
                    {
                        'param': arg_name,
                        'scenario': 'empty_dict',
                        'value': '{}',
                        'description': f'{arg_name}为空字典'
                    },
                    {
                        'param': arg_name,
                        'scenario': 'none',
                        'value': 'None',
                        'description': f'{arg_name}为None'
                    }
                ])
            else:
                # 未知类型的通用边界场景
                edge_cases.extend([
                    {
                        'param': arg_name,
                        'scenario': 'none',
                        'value': 'None',
                        'description': f'{arg_name}为None'
                    }
                ])

        return edge_cases

    def _generate_edge_case_test_code(self, function_name: str, edge_cases: List[Dict]) -> str:
        """生成边界测试代码"""
        test_code = f'''import pytest


class Test{function_name.capitalize()}EdgeCases:
    """{function_name}函数的边界测试"""

'''

        # 按参数分组边界场景
        param_groups = {}
        for case in edge_cases:
            param = case['param']
            if param not in param_groups:
                param_groups[param] = []
            param_groups[param].append(case)

        # 为每个参数生成测试方法
        for param, cases in param_groups.items():
            test_code += f'    @pytest.mark.parametrize("{param}", [\n'
            for case in cases:
                test_code += f'        ({case["value"]}),  # {case["description"]}\n'
            test_code += f'    ])\n'
            test_code += f'    def test_{function_name}_{param}_edge_cases(self, {param}):\n'
            test_code += f'        """测试{function_name}在不同{param}值下的行为"""\n'
            test_code += f'        # TODO: 实现测试逻辑\n'
            test_code += f'        result = {function_name}({param}={param} if {param} != "None" else None)\n'
            test_code += f'        # TODO: 添加断言\n'
            test_code += f'        assert result is not None\n\n'

        return test_code

    @tool
    def check_test_coverage(self, test_code: str = None, test_file_path: str = None) -> Dict[str, Any]:
        """
        评估测试覆盖率

        Args:
            test_code: 测试代码字符串
            test_file_path: 测试文件路径

        Returns:
            包含以下字段的字典：
            - functions_covered: 被测试的函数数量
            - total_functions: 总函数数量
            - coverage_rate: 覆盖率百分比
            - uncovered_functions: 未测试的函数列表
            - recommendations: 改进建议
        """
        # 获取测试代码
        if test_file_path:
            with open(test_file_path, 'r', encoding='utf-8') as f:
                test_code = f.read()
        elif not test_code:
            return {
                'error': '必须提供test_code或test_file_path'
            }

        # 获取源代码中的所有函数
        source_functions = {func['name'] for func in self._get_functions()}

        # 从测试代码中提取被测试的函数
        tested_functions = set()
        test_tree = ast.parse(test_code)

        for node in ast.walk(test_tree):
            if isinstance(node, ast.FunctionDef):
                func_name = node.name
                # 从测试函数名中提取被测试的函数名
                # 例如: test_add_basic -> add
                if func_name.startswith('test_'):
                    parts = func_name[5:].split('_')
                    if parts:
                        tested_functions.add(parts[0])

        # 计算覆盖率
        total_functions = len(source_functions)
        functions_covered = len(source_functions & tested_functions)
        coverage_rate = (functions_covered / total_functions * 100) if total_functions > 0 else 0

        # 找出未测试的函数
        uncovered_functions = list(source_functions - tested_functions)

        # 生成建议
        recommendations = []
        if coverage_rate < 50:
            recommendations.append("测试覆盖率较低，建议为主要功能添加测试")
        if coverage_rate < 80:
            recommendations.append("建议为辅助函数添加测试")

        for func in uncovered_functions:
            recommendations.append(f"建议为 {func} 函数添加测试")

        return {
            'functions_covered': functions_covered,
            'total_functions': total_functions,
            'coverage_rate': round(coverage_rate, 2),
            'uncovered_functions': uncovered_functions,
            'tested_functions': list(tested_functions),
            'recommendations': recommendations
        }

    @tool
    def generate_all_tests(self) -> Dict[str, Any]:
        """
        为源代码中的所有函数生成测试

        Returns:
            包含以下字段的字典：
            - test_code: 完整的测试代码
            - functions_tested: 被测试的函数列表
            - total_tests: 生成的测试数量
        """
        functions = self._get_functions()
        all_test_code = []
        test_count = 0

        for func in functions:
            result = self.generate_test(func['name'])
            if result.get('success'):
                all_test_code.append(result['test_code'])
                test_count += len(result.get('test_cases', []))

        # 合并所有测试代码
        combined_code = '\n\n'.join(all_test_code)

        return {
            'test_code': combined_code,
            'functions_tested': [func['name'] for func in functions],
            'total_tests': test_count
        }

    @tool
    def get_function_info(self, function_name: str) -> Dict[str, Any]:
        """
        获取函数的详细信息

        Args:
            function_name: 函数名

        Returns:
            函数详细信息字典
        """
        functions = self._get_functions()
        for func in functions:
            if func['name'] == function_name:
                return func
        return {'error': f'未找到函数: {function_name}'}
