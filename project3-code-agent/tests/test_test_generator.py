"""测试TestGenerator类的单元测试"""

import pytest
import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tools.test_generator import TestGenerator, tool


# 测试用的示例代码
SAMPLE_CODE = '''"""示例模块用于测试TestGenerator"""

from typing import List, Optional


def add(a: int, b: int) -> int:
    """
    将两个整数相加

    Args:
        a: 第一个整数
        b: 第二个整数

    Returns:
        两数之和
    """
    return a + b


def divide(a: float, b: float) -> float:
    """
    除法运算

    Args:
        a: 被除数
        b: 除数

    Returns:
        除法结果

    Raises:
        ZeroDivisionError: 当b为0时
    """
    if b == 0:
        raise ZeroDivisionError("Cannot divide by zero")
    return a / b


def process_items(items: List[str]) -> List[str]:
    """
    处理字符串列表

    Args:
        items: 字符串列表

    Returns:
        处理后的字符串列表
    """
    if not items:
        return []
    return [item.strip() for item in items]


def no_return_function(value: str) -> None:
    """没有返回值的函数"""
    print(value)


class Calculator:
    """计算器类"""

    def multiply(self, a: int, b: int) -> int:
        """乘法运算"""
        return a * b
'''


class TestTestGenerator:
    """TestGenerator类的测试套件"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.generator = TestGenerator(source_code=SAMPLE_CODE)

    def test_initialization_with_source_code(self):
        """测试使用源代码字符串初始化"""
        gen = TestGenerator(source_code=SAMPLE_CODE)
        assert gen.source_code == SAMPLE_CODE
        assert gen.tree is not None

    def test_initialization_requires_source_or_file(self):
        """测试初始化时必须提供源代码或文件路径"""
        with pytest.raises(ValueError, match="必须提供source_code或file_path"):
            TestGenerator()

    def test_get_functions(self):
        """测试获取函数列表"""
        functions = self.generator._get_functions()
        function_names = [f['name'] for f in functions]

        assert 'add' in function_names
        assert 'divide' in function_names
        assert 'process_items' in function_names
        assert 'no_return_function' in function_names

    def test_function_info_structure(self):
        """测试函数信息结构"""
        functions = self.generator._get_functions()
        add_func = next(f for f in functions if f['name'] == 'add')

        assert 'name' in add_func
        assert 'args' in add_func
        assert 'docstring' in add_func
        assert 'lineno' in add_func
        assert len(add_func['args']) == 2

    def test_get_function_with_has_return(self):
        """测试检测函数是否有返回值"""
        functions = self.generator._get_functions()

        add_func = next(f for f in functions if f['name'] == 'add')
        assert add_func['has_return'] == True

        no_return_func = next(f for f in functions if f['name'] == 'no_return_function')
        assert no_return_func['has_return'] == False

    def test_get_function_source(self):
        """测试获取函数源代码"""
        source = self.generator._get_function_source('add')
        assert 'def add' in source
        assert 'return a + b' in source

    def test_extract_test_cases(self):
        """测试从测试代码中提取测试用例"""
        test_code = '''
def test_add_basic():
    pass

def test_add_negative():
    pass

def test_divide_by_zero():
    pass
'''
        cases = self.generator._extract_test_cases(test_code)
        assert 'test_add_basic' in cases
        assert 'test_add_negative' in cases
        assert 'test_divide_by_zero' in cases

    def test_generate_test_for_existing_function(self):
        """测试为存在的函数生成测试"""
        result = self.generator.generate_test('add')
        # @tool装饰器会包装结果
        actual_result = result.get('result', result)

        assert actual_result['success'] == True
        assert actual_result['function_name'] == 'add'
        assert actual_result['test_code'] is not None
        assert isinstance(actual_result['test_cases'], list)
        assert 'test_' in actual_result['test_code']

    def test_generate_test_for_nonexistent_function(self):
        """测试为不存在的函数生成测试"""
        result = self.generator.generate_test('nonexistent_function')
        actual_result = result.get('result', result)

        assert actual_result['success'] == False
        assert 'error' in actual_result

    def test_generate_test_code_contains_pytest_imports(self):
        """测试生成的测试代码包含pytest导入"""
        result = self.generator.generate_test('add')
        actual_result = result.get('result', result)
        test_code = actual_result['test_code']

        assert 'import pytest' in test_code

    def test_generate_test_code_class_structure(self):
        """测试生成的测试代码包含测试类"""
        result = self.generator.generate_test('add')
        actual_result = result.get('result', result)
        test_code = actual_result['test_code']

        assert 'class Test' in test_code or 'def test_' in test_code

    def test_analyze_edge_cases_for_int_params(self):
        """测试分析整数参数的边界情况"""
        functions = self.generator._get_functions()
        add_func = next(f for f in functions if f['name'] == 'add')

        edge_cases = self.generator._analyze_edge_cases(add_func)

        # 应该包含整数的边界情况
        scenarios = [case['scenario'] for case in edge_cases]
        assert 'zero' in scenarios or 'negative' in scenarios

    def test_analyze_edge_cases_for_str_params(self):
        """测试分析字符串参数的边界情况"""
        # 修改示例代码以包含字符串参数函数
        code_with_str = SAMPLE_CODE + '''

def greet(name: str) -> str:
    return f"Hello, {name}"
'''
        gen = TestGenerator(source_code=code_with_str)
        functions = gen._get_functions()
        greet_func = next(f for f in functions if f['name'] == 'greet')

        edge_cases = gen._analyze_edge_cases(greet_func)

        scenarios = [case['scenario'] for case in edge_cases]
        assert 'empty_string' in scenarios or 'none' in scenarios

    def test_generate_edge_cases(self):
        """测试生成边界测试场景"""
        result = self.generator.generate_edge_cases('add')
        actual_result = result.get('result', result)

        assert actual_result['function_name'] == 'add'
        assert 'edge_cases' in actual_result
        assert 'test_code' in actual_result
        assert isinstance(actual_result['edge_cases'], list)

    def test_check_test_coverage(self):
        """测试检查测试覆盖率"""
        # 创建一个测试代码，只测试了部分函数
        partial_test_code = '''
import pytest

def test_add():
    assert add(1, 2) == 3

def test_process_items():
    assert process_items(["a", "b"]) == ["a", "b"]
'''
        result = self.generator.check_test_coverage(test_code=partial_test_code)
        actual_result = result.get('result', result)

        assert 'functions_covered' in actual_result
        assert 'total_functions' in actual_result
        assert 'coverage_rate' in actual_result
        assert actual_result['total_functions'] > 0
        assert 0 <= actual_result['coverage_rate'] <= 100

    def test_check_test_coverage_uncovered_functions(self):
        """测试检查未覆盖的函数"""
        test_code = '''
def test_add():
    pass
'''
        result = self.generator.check_test_coverage(test_code=test_code)
        actual_result = result.get('result', result)

        assert 'uncovered_functions' in actual_result
        # add被测试了，所以不应该在uncovered中
        assert 'add' not in actual_result.get('uncovered_functions', [])

    def test_check_test_coverage_recommendations(self):
        """测试覆盖率建议"""
        test_code = '''
def test_add():
    pass
'''
        result = self.generator.check_test_coverage(test_code=test_code)
        actual_result = result.get('result', result)

        assert 'recommendations' in actual_result
        assert isinstance(actual_result['recommendations'], list)

    def test_generate_all_tests(self):
        """测试为所有函数生成测试"""
        result = self.generator.generate_all_tests()
        actual_result = result.get('result', result)

        assert 'test_code' in actual_result
        assert 'functions_tested' in actual_result
        assert 'total_tests' in actual_result
        assert len(actual_result['functions_tested']) > 0
        assert actual_result['total_tests'] >= 0

    def test_get_function_info(self):
        """测试获取函数详细信息"""
        result = self.generator.get_function_info('add')
        actual_result = result.get('result', result)

        assert actual_result['name'] == 'add'
        assert 'args' in actual_result
        assert 'docstring' in actual_result

    def test_get_function_info_nonexistent(self):
        """测试获取不存在函数的信息"""
        result = self.generator.get_function_info('nonexistent')
        actual_result = result.get('result', result)

        assert 'error' in actual_result

    def test_tool_decorator(self):
        """测试tool装饰器"""
        @tool
        def sample_function():
            return {"data": "test"}

        result = sample_function()
        assert result['tool'] == 'sample_function'
        assert result['result']['data'] == 'test'

    def test_extract_code_from_response_with_markdown(self):
        """测试从markdown响应中提取代码"""
        response = '''以下是生成的测试代码：

```python
import pytest

def test_add():
    assert True
```

希望这对你有帮助。'''
        code = self.generator._extract_code_from_response(response)
        assert 'import pytest' in code
        assert 'def test_add' in code
        assert '```' not in code

    def test_extract_code_from_response_without_markdown(self):
        """测试从没有markdown的响应中提取代码"""
        response = '''import pytest

def test_add():
    assert True'''
        code = self.generator._extract_code_from_response(response)
        assert 'import pytest' in code

    def test_get_classes(self):
        """测试获取类信息"""
        classes = self.generator._get_classes()
        class_names = [c['name'] for c in classes]

        assert 'Calculator' in class_names

    def test_class_info_structure(self):
        """测试类信息结构"""
        classes = self.generator._get_classes()
        calc_class = next((c for c in classes if c['name'] == 'Calculator'), None)

        assert calc_class is not None
        assert 'name' in calc_class
        assert 'methods' in calc_class
        assert 'lineno' in calc_class
        assert 'multiply' in calc_class['methods']

    def test_edge_case_test_code_format(self):
        """测试边界测试代码格式"""
        result = self.generator.generate_edge_cases('add')
        actual_result = result.get('result', result)
        test_code = actual_result['test_code']

        assert 'import pytest' in test_code
        assert '@pytest.mark.parametrize' in test_code
        assert 'def test_' in test_code


class TestTestGeneratorWithFile:
    """TestGenerator文件操作的测试套件"""

    def test_initialization_with_file_path(self, tmp_path):
        """测试使用文件路径初始化"""
        # 创建临时文件
        test_file = tmp_path / "test_module.py"
        test_file.write_text(SAMPLE_CODE)

        gen = TestGenerator(file_path=str(test_file))
        assert gen.source_code == SAMPLE_CODE
        assert gen.file_path == str(test_file)

    def test_check_coverage_with_file(self, tmp_path):
        """测试使用文件检查覆盖率"""
        # 创建源文件
        source_file = tmp_path / "source.py"
        source_file.write_text(SAMPLE_CODE)

        # 创建测试文件
        test_file = tmp_path / "test_source.py"
        test_file.write_text('''
def test_add():
    pass
''')

        gen = TestGenerator(file_path=str(source_file))
        result = gen.check_test_coverage(test_file_path=str(test_file))
        actual_result = result.get('result', result)

        assert 'coverage_rate' in actual_result


class TestTestGeneratorEdgeCases:
    """TestGenerator边界情况测试"""

    def test_empty_source_code(self):
        """测试空源代码 - 空字符串被当作falsy所以触发第一个验证"""
        with pytest.raises(ValueError, match="必须提供source_code或file_path"):
            TestGenerator(source_code="")

    def test_invalid_source_code(self):
        """测试无效源代码"""
        with pytest.raises(ValueError, match="代码解析失败"):
            TestGenerator(source_code="def foo(\n")  # 不完整的函数

    def test_invalid_syntax(self):
        """测试无效语法"""
        # 空字符串在当前实现中被当作没有提供source_code
        # 所以这里测试一个非空但语法错误的代码
        with pytest.raises(ValueError, match="代码解析失败"):
            TestGenerator(source_code="def foo(\n")  # 不完整的函数

    def test_function_with_no_args(self):
        """测试无参数函数"""
        code = '''
def no_args():
    return 42
'''
        gen = TestGenerator(source_code=code)
        result = gen.generate_test('no_args')
        actual_result = result.get('result', result)

        assert actual_result['success'] == True

    def test_function_with_optional_params(self):
        """测试带有可选参数的函数"""
        code = '''
from typing import Optional

def optional_param(name: Optional[str] = None) -> str:
    return name or "default"
'''
        gen = TestGenerator(source_code=code)
        functions = gen._get_functions()
        func = next(f for f in functions if f['name'] == 'optional_param')

        assert len(func['args']) == 1
