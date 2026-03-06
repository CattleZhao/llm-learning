"""代码分析工具模块的测试"""

import os
import sys

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tools.code_analyzer import CodeAnalyzer


# 测试用的示例代码
SAMPLE_CODE = '''
"""这是一个示例Python模块"""

import os
import sys
from typing import List, Dict
from collections import defaultdict

# 这是一个全局变量
MAX_COUNT = 100


def calculate_sum(a: int, b: int) -> int:
    """计算两个数的和"""
    return a + b


def greet(name: str, greeting: str = "Hello") -> str:
    """生成问候语"""
    return f"{greeting}, {name}!"


class DataProcessor:
    """数据处理类"""

    def __init__(self, data: List):
        self.data = data
        self.processed = False

    def process(self):
        """处理数据"""
        if not self.processed:
            for item in self.data:
                if item > 0:
                    yield item * 2
                else:
                    yield item

    def get_stats(self) -> Dict:
        """获取统计信息"""
        stats = {
            'count': len(self.data),
            'processed': self.processed
        }
        try:
            stats['sum'] = sum(self.data)
        except Exception as e:
            stats['error'] = str(e)
        return stats


# 全局函数
def main():
    """主函数"""
    processor = DataProcessor([1, 2, 3])
    results = list(processor.process())
    print(f"Results: {results}")
    print(f"Stats: {processor.get_stats()}")


if __name__ == "__main__":
    main()
'''


def test_analyze_functions():
    """测试函数分析功能"""
    print("\n=== 测试函数分析 ===")
    analyzer = CodeAnalyzer(source_code=SAMPLE_CODE)

    result = analyzer.analyze_functions()
    functions = result['result']  # @tool装饰器返回 {'tool': ..., 'result': ...}
    print(f"找到 {len(functions)} 个函数:")

    for func in functions:
        method_indicator = "方法" if func['is_method'] else "函数"
        print(f"  - {func['name']} ({method_indicator})")
        print(f"    参数数量: {func['args_count']}")
        print(f"    位置: 第 {func['line_number']} 行")

    # 验证结果
    assert len(functions) == 6  # calculate_sum, greet, __init__, process, get_stats, main
    assert any(f['name'] == 'calculate_sum' for f in functions)
    assert any(f['name'] == 'process' and f['is_method'] for f in functions)
    print("✓ 函数分析测试通过")


def test_count_lines():
    """测试行数统计功能"""
    print("\n=== 测试行数统计 ===")
    analyzer = CodeAnalyzer(source_code=SAMPLE_CODE)

    result = analyzer.count_lines()
    lines = result['result']  # @tool装饰器返回 {'tool': ..., 'result': ...}
    print(f"总行数: {lines['total']}")
    print(f"非空行数: {lines['non_empty']}")
    print(f"注释行数: {lines['comments']}")
    print(f"代码行数: {lines['code']}")

    # 验证结果
    assert lines['total'] > 0
    assert lines['non_empty'] > 0
    assert lines['code'] > 0
    print("✓ 行数统计测试通过")


def test_get_imports():
    """测试导入语句分析功能"""
    print("\n=== 测试导入语句分析 ===")
    analyzer = CodeAnalyzer(source_code=SAMPLE_CODE)

    result = analyzer.get_imports()
    imports = result['result']  # @tool装饰器返回 {'tool': ..., 'result': ...}
    print(f"标准import ({len(imports['standard_imports'])}):")
    for imp in imports['standard_imports']:
        alias_str = f" as {imp['alias']}" if imp['alias'] else ""
        print(f"  - import {imp['module']}{alias_str}")

    print(f"\nFrom import ({len(imports['from_imports'])}):")
    for imp in imports['from_imports']:
        imports_str = ", ".join([
            f"{i['name']}" + (f" as {i['alias']}" if i['alias'] else "")
            for i in imp['imports']
        ])
        print(f"  - from {imp['module']} import {imports_str}")

    # 验证结果
    assert len(imports['standard_imports']) == 2  # os, sys
    assert len(imports['from_imports']) == 2  # typing, collections
    print("✓ 导入语句分析测试通过")


def test_analyze_classes():
    """测试类分析功能"""
    print("\n=== 测试类分析 ===")
    analyzer = CodeAnalyzer(source_code=SAMPLE_CODE)

    result = analyzer.analyze_classes()
    classes = result['result']  # @tool装饰器返回 {'tool': ..., 'result': ...}
    print(f"找到 {len(classes)} 个类:")

    for cls in classes:
        print(f"  - {cls['name']}")
        print(f"    位置: 第 {cls['line_number']} 行")
        print(f"    方法数量: {cls['methods_count']}")
        print(f"    基类: {cls['base_classes'] or '无'}")

    # 验证结果
    assert len(classes) == 1
    assert classes[0]['name'] == 'DataProcessor'
    assert classes[0]['methods_count'] == 3  # __init__, process, get_stats
    print("✓ 类分析测试通过")


def test_get_complexity():
    """测试复杂度分析功能"""
    print("\n=== 测试复杂度分析 ===")
    analyzer = CodeAnalyzer(source_code=SAMPLE_CODE)

    result = analyzer.get_complexity()
    complexity = result['result']  # @tool装饰器返回 {'tool': ..., 'result': ...}
    print(f"圈复杂度: {complexity['cyclomatic_complexity']}")
    print(f"复杂度等级: {complexity['level']}")

    # 验证结果
    assert complexity['cyclomatic_complexity'] > 0
    assert complexity['level'] in ['low', 'moderate', 'high', 'very_high']
    print("✓ 复杂度分析测试通过")


def test_get_full_report():
    """测试完整报告功能"""
    print("\n=== 测试完整报告 ===")
    analyzer = CodeAnalyzer(source_code=SAMPLE_CODE)

    result = analyzer.get_full_report()
    report = result['result']  # @tool装饰器返回 {'tool': ..., 'result': ...}
    print("完整报告:")
    print(f"  函数数量: {len(report['functions'])}")
    print(f"  类数量: {len(report['classes'])}")
    print(f"  总行数: {report['lines']['total']}")
    print(f"  圈复杂度: {report['complexity']['cyclomatic_complexity']}")

    # 验证报告结构
    assert 'functions' in report
    assert 'classes' in report
    assert 'lines' in report
    assert 'imports' in report
    assert 'complexity' in report
    print("✓ 完整报告测试通过")


def test_tool_decorator():
    """测试@tool装饰器功能"""
    print("\n=== 测试@tool装饰器 ===")
    analyzer = CodeAnalyzer(source_code=SAMPLE_CODE)

    result = analyzer.analyze_functions()

    # 验证装饰器添加了tool元数据
    assert 'tool' in result
    assert 'result' in result
    assert result['tool'] == 'analyze_functions'
    print(f"工具名称: {result['tool']}")
    print(f"返回结果类型: {type(result['result'])}")
    print("✓ @tool装饰器测试通过")


def test_file_path_input():
    """测试从文件路径加载代码"""
    print("\n=== 测试文件路径输入 ===")

    # 创建临时测试文件
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(SAMPLE_CODE)
        temp_path = f.name

    try:
        analyzer = CodeAnalyzer(file_path=temp_path)
        result = analyzer.analyze_functions()
        print(f"从文件加载并分析，找到 {len(result['result'])} 个函数")
        assert len(result['result']) > 0
        print("✓ 文件路径输入测试通过")
    finally:
        os.unlink(temp_path)


def run_all_tests():
    """运行所有测试"""
    print("=" * 50)
    print("开始运行代码分析器测试")
    print("=" * 50)

    try:
        test_analyze_functions()
        test_count_lines()
        test_get_imports()
        test_analyze_classes()
        test_get_complexity()
        test_get_full_report()
        test_tool_decorator()
        test_file_path_input()

        print("\n" + "=" * 50)
        print("✅ 所有测试通过!")
        print("=" * 50)
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        raise
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()
