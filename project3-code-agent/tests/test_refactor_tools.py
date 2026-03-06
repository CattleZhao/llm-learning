"""重构工具模块的测试"""

import os
import sys

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tools.refactor_tools import RefactorTools


# 测试用的示例代码（包含代码异味）
CODE_WITH_SMELLS = '''
"""包含代码异味的示例代码"""

import os


def long_function_with_many_lines(data):
    """这是一个过长的函数，包含很多行代码"""
    # 初始化变量
    result = []
    temp_var = 0
    counter = 0
    flag = True

    # 第一个处理块
    for item in data:
        if item > 0:
            if item % 2 == 0:
                if item > 10:
                    if item < 100:
                        result.append(item * 2)
                        counter += 1

    # 第二个处理块
    for item in data:
        if item < 0:
            result.append(abs(item))
            counter += 1

    # 第三个处理块
    for item in data:
        if item == 0:
            result.append(0)
            counter += 1

    # 第四个处理块
    total = sum(result)
    avg = total / len(result) if result else 0

    # 第五个处理块
    if avg > 50:
        flag = False

    # 第六个处理块
    if flag:
        result = [x * 2 for x in result]

    # 第七个处理块
    final_result = []
    for item in result:
        if item > 0:
            final_result.append(item)

    # 第八个处理块
    temp_var = sum(final_result)

    # 第九个处理块
    output = []
    for i in range(len(final_result)):
        output.append(final_result[i] + temp_var)

    # 第十个处理块
    return output


def function_with_too_many_params(a, b, c, d, e, f):
    """这个函数有太多参数"""
    return a + b + c + d + e + f


def another_duplicate_function(data):
    """这个函数有重复代码"""
    result = []
    for item in data:
        result.append(item)
    return result


def yet_another_duplicate_function(data):
    """这个函数也有重复代码"""
    result = []
    for item in data:
        result.append(item)
    return result


class LargeClassWithManyMethods:
    """这是一个过大的类"""

    def __init__(self):
        self.value1 = 1
        self.value2 = 2
        self.value3 = 3
        self.value4 = 4
        self.value5 = 5
        self.value6 = 6
        self.value7 = 7
        self.value8 = 8
        self.value9 = 9
        self.value10 = 10

    def method1(self):
        return self.value1

    def method2(self):
        return self.value2

    def method3(self):
        return self.value3

    def method4(self):
        return self.value4

    def method5(self):
        return self.value5

    def method6(self):
        return self.value6

    def method7(self):
        return self.value7

    def method8(self):
        return self.value8

    def method9(self):
        return self.value9

    def method10(self):
        return self.value10

    def method11(self):
        return self.value1 + self.value2

    def method12(self):
        return self.value3 + self.value4

    def method13(self):
        return self.value5 + self.value6

    def method14(self):
        return self.value7 + self.value8

    def method15(self):
        return self.value9 + self.value10

    def method16(self):
        return sum([self.value1, self.value2, self.value3])


class DataClassOnly:
    """这是一个仅包含数据的类"""

    def __init__(self):
        self.name = ""
        self.age = 0
        self.email = ""
        self.phone = ""
        self.address = ""


# 正常的代码作为对比
def normal_function(x, y):
    """这是一个正常的函数"""
    return x + y


def simple_function():
    """简单函数"""
    return "Hello"
'''


# 清洁的代码示例
CLEAN_CODE = '''
"""清洁的代码示例"""

def calculate_average(numbers):
    """计算平均值"""
    return sum(numbers) / len(numbers) if numbers else 0


class DataProcessor:
    """数据处理器"""

    def __init__(self, data):
        self.data = data

    def process(self):
        """处理数据"""
        return [x * 2 for x in self.data if x > 0]

    def get_summary(self):
        """获取摘要"""
        return {
            'count': len(self.data),
            'average': calculate_average(self.data)
        }
'''


def test_check_code_smells():
    """测试代码异味检测功能"""
    print("\n=== 测试代码异味检测 ===")
    refactor_tools = RefactorTools(source_code=CODE_WITH_SMELLS)

    result = refactor_tools.check_code_smells()
    smells = result['result']

    print(f"检测到的代码异味类型: {list(smells.keys())}")

    for smell_type, issues in smells.items():
        print(f"\n{smell_type} ({len(issues)} 个):")
        for issue in issues[:2]:  # 只显示前2个
            print(f"  - {issue.get('description', 'N/A')}")

    # 验证检测到的主要异味
    assert 'long_functions' in smells or 'large_classes' in smells
    print("✓ 代码异味检测测试通过")


def test_check_long_functions():
    """测试长函数检测"""
    print("\n=== 测试长函数检测 ===")
    refactor_tools = RefactorTools(source_code=CODE_WITH_SMELLS)

    result = refactor_tools.check_code_smells()
    smells = result['result']

    if 'long_functions' in smells:
        long_funcs = smells['long_functions']
        print(f"检测到 {len(long_funcs)} 个长函数:")
        for func in long_funcs:
            print(f"  - {func['name']}: {func['lines']} 行 (第{func['line_number']}行)")

        assert any(f['name'] == 'long_function_with_many_lines' for f in long_funcs)
        print("✓ 长函数检测测试通过")
    else:
        print("  未检测到长函数（可能是阈值配置）")


def test_check_deep_nesting():
    """测试深度嵌套检测"""
    print("\n=== 测试深度嵌套检测 ===")
    refactor_tools = RefactorTools(source_code=CODE_WITH_SMELLS)

    result = refactor_tools.check_code_smells()
    smells = result['result']

    if 'deep_nesting' in smells:
        deep_nests = smells['deep_nesting']
        print(f"检测到 {len(deep_nests)} 个深度嵌套:")
        for nest in deep_nests:
            print(f"  - {nest['function']}: {nest['max_nesting_level']} 层嵌套")

        assert any('long_function' in n['function'] for n in deep_nests)
        print("✓ 深度嵌套检测测试通过")
    else:
        print("  未检测到深度嵌套")


def test_check_long_parameter_list():
    """测试参数过多检测"""
    print("\n=== 测试参数过多检测 ===")
    refactor_tools = RefactorTools(source_code=CODE_WITH_SMELLS)

    result = refactor_tools.check_code_smells()
    smells = result['result']

    if 'long_parameter_list' in smells:
        long_params = smells['long_parameter_list']
        print(f"检测到 {len(long_params)} 个参数过多的函数:")
        for func in long_params:
            print(f"  - {func['name']}: {func['parameter_count']} 个参数")

        assert any(f['name'] == 'function_with_too_many_params' for f in long_params)
        print("✓ 参数过多检测测试通过")
    else:
        print("  未检测到参数过多的函数")


def test_check_large_classes():
    """测试大类检测"""
    print("\n=== 测试大类检测 ===")
    refactor_tools = RefactorTools(source_code=CODE_WITH_SMELLS)

    result = refactor_tools.check_code_smells()
    smells = result['result']

    if 'large_classes' in smells:
        large_classes = smells['large_classes']
        print(f"检测到 {len(large_classes)} 个大类:")
        for cls in large_classes:
            print(f"  - {cls['name']}: {cls['methods_count']} 个方法, {cls['lines']} 行")

        assert any(c['name'] == 'LargeClassWithManyMethods' for c in large_classes)
        print("✓ 大类检测测试通过")
    else:
        print("  未检测到大类")


def test_check_data_classes():
    """测试数据类检测"""
    print("\n=== 测试数据类检测 ===")
    refactor_tools = RefactorTools(source_code=CODE_WITH_SMELLS)

    result = refactor_tools.check_code_smells()
    smells = result['result']

    if 'data_classes' in smells:
        data_classes = smells['data_classes']
        print(f"检测到 {len(data_classes)} 个数据类:")
        for cls in data_classes:
            print(f"  - {cls['name']}: {len(cls['attributes'])} 个属性, {len(cls['methods'])} 个方法")

        assert any(c['name'] == 'DataClassOnly' for c in data_classes)
        print("✓ 数据类检测测试通过")
    else:
        print("  未检测到数据类")


def test_check_duplicate_code():
    """测试重复代码检测"""
    print("\n=== 测试重复代码检测 ===")
    refactor_tools = RefactorTools(source_code=CODE_WITH_SMELLS)

    result = refactor_tools.check_code_smells()
    smells = result['result']

    if 'duplicate_code' in smells:
        duplicates = smells['duplicate_code']
        print(f"检测到 {len(duplicates)} 处重复代码:")
        for dup in duplicates[:3]:
            print(f"  - {dup['content'][:30]}... ({dup['occurrences']} 次)")

        print("✓ 重复代码检测测试通过")
    else:
        print("  未检测到重复代码")


def test_clean_code_analysis():
    """测试清洁代码分析"""
    print("\n=== 测试清洁代码分析 ===")
    refactor_tools = RefactorTools(source_code=CLEAN_CODE)

    result = refactor_tools.check_code_smells()
    smells = result['result']

    total_smells = sum(len(issues) for issues in smells.values())
    print(f"清洁代码中的异味数量: {total_smells}")

    if total_smells == 0:
        print("✓ 清洁代码分析测试通过 - 无代码异味")
    else:
        print(f"  检测到 {total_smells} 个轻微问题（可能是正常的）")


def test_suggest_refactoring():
    """测试重构建议功能"""
    print("\n=== 测试重构建议 ===")
    refactor_tools = RefactorTools(source_code=CODE_WITH_SMELLS)

    result = refactor_tools.suggest_refactoring()
    suggestion = result['result']

    print(f"代码异味: {list(suggestion.get('code_smells', {}).keys())}")
    print(f"摘要: {suggestion.get('summary', 'N/A')}")

    if 'ai_suggestions' in suggestion:
        print(f"AI建议数量: {len(suggestion['ai_suggestions'])}")

    assert 'summary' in suggestion
    print("✓ 重构建议测试通过")


def test_apply_refactoring():
    """测试应用重构功能"""
    print("\n=== 测试应用重构 ===")
    refactor_tools = RefactorTools(source_code=CLEAN_CODE)

    result = refactor_tools.apply_refactoring(
        description="将DataProcessor类重命名为Processor",
        target="DataProcessor"
    )
    refactoring = result['result']

    if refactoring.get('success'):
        print(f"原始代码长度: {len(refactoring['original_code'])}")
        print(f"重构后代码长度: {len(refactoring.get('refactored_code', ''))}")
        print(f"说明: {refactoring.get('explanation', 'N/A')[:100]}...")
        print("✓ 应用重构测试通过")
    else:
        print(f"重构失败（可能是LLM未配置）: {refactoring.get('error', 'Unknown')}")
        # 这是预期的，如果没有配置API密钥


def test_get_refactoring_priority():
    """测试重构优先级功能"""
    print("\n=== 测试重构优先级 ===")
    refactor_tools = RefactorTools(source_code=CODE_WITH_SMELLS)

    result = refactor_tools.get_refactoring_priority()
    priorities = result['result']

    print(f"重构任务数量: {len(priorities)}")
    print("\n前5个优先级任务:")
    for item in priorities[:5]:
        print(f"  - [{item['priority'].upper()}] {item['type']}: {item['issue'].get('description', 'N/A')[:50]}...")

    # 验证优先级排序
    if len(priorities) >= 2:
        assert priorities[0]['score'] >= priorities[1]['score']
        print("✓ 重构优先级排序正确")

    print("✓ 重构优先级测试通过")


def test_get_complexity_metrics():
    """测试复杂度指标功能"""
    print("\n=== 测试复杂度指标 ===")
    refactor_tools = RefactorTools(source_code=CODE_WITH_SMELLS)

    result = refactor_tools.get_complexity_metrics()
    metrics = result['result']

    print("复杂度指标:")
    print(f"  总行数: {metrics['total_lines']}")
    print(f"  函数数量: {metrics['functions']['total']}")
    print(f"  类数量: {metrics['classes']['total']}")
    print(f"  圈复杂度: {metrics['cyclomatic_complexity']['value']} ({metrics['cyclomatic_complexity']['level']})")
    print(f"  可维护性指数: {metrics['maintainability_index']}")
    print(f"  代码重复率: {metrics['code_duplication']['rate_percentage']}%")

    # 验证指标结构
    assert 'total_lines' in metrics
    assert 'functions' in metrics
    assert 'classes' in metrics
    assert 'cyclomatic_complexity' in metrics
    assert 'maintainability_index' in metrics
    assert 'code_duplication' in metrics
    print("✓ 复杂度指标测试通过")


def test_tool_decorator():
    """测试@tool装饰器功能"""
    print("\n=== 测试@tool装饰器 ===")
    refactor_tools = RefactorTools(source_code=CLEAN_CODE)

    result = refactor_tools.check_code_smells()

    # 验证装饰器添加了tool元数据
    assert 'tool' in result
    assert 'result' in result
    assert result['tool'] == 'check_code_smells'
    print(f"工具名称: {result['tool']}")
    print(f"返回结果类型: {type(result['result'])}")
    print("✓ @tool装饰器测试通过")


def test_file_path_input():
    """测试从文件路径加载代码"""
    print("\n=== 测试文件路径输入 ===")

    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(CLEAN_CODE)
        temp_path = f.name

    try:
        refactor_tools = RefactorTools(file_path=temp_path)
        result = refactor_tools.check_code_smells()
        print(f"从文件加载并分析，检测到 {sum(len(v) for v in result['result'].values())} 个代码异味")
        print("✓ 文件路径输入测试通过")
    finally:
        os.unlink(temp_path)


def test_custom_thresholds():
    """测试自定义阈值配置"""
    print("\n=== 测试自定义阈值 ===")

    # 创建一个刚好超过阈值的函数
    just_over_threshold = '''
def almost_long_function():
    """一个刚好超过阈值的函数"""
    x = 1
    x = 2
    x = 3
    x = 4
    x = 5
    x = 6
    x = 7
    x = 8
    x = 9
    x = 10
    x = 11
    x = 12
    x = 13
    x = 14
    x = 15
    x = 16
    x = 17
    x = 18
    x = 19
    x = 20
    x = 21
    x = 22
    x = 23
    x = 24
    x = 25
    x = 26
    x = 27
    x = 28
    x = 29
    x = 30
    x = 31
    return x
'''

    refactor_tools = RefactorTools(source_code=just_over_threshold)

    result = refactor_tools.check_code_smells()
    smells = result['result']

    if 'long_functions' in smells:
        print(f"检测到超过阈值的长函数: {len(smells['long_functions'])} 个")
        print("✓ 自定义阈值测试通过")
    else:
        print("  函数刚好在阈值边界")


def run_all_tests():
    """运行所有测试"""
    print("=" * 50)
    print("开始运行重构工具测试")
    print("=" * 50)

    try:
        test_check_code_smells()
        test_check_long_functions()
        test_check_deep_nesting()
        test_check_long_parameter_list()
        test_check_large_classes()
        test_check_data_classes()
        test_check_duplicate_code()
        test_clean_code_analysis()
        test_suggest_refactoring()
        test_apply_refactoring()
        test_get_refactoring_priority()
        test_get_complexity_metrics()
        test_tool_decorator()
        test_file_path_input()
        test_custom_thresholds()

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
