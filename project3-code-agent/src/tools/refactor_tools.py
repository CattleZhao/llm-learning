"""代码重构工具模块 - 提供代码分析和重构建议"""

import ast
import re
from typing import Dict, List, Any, Optional
from functools import wraps

from src.llm_client import SimpleLLMClient


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


class RefactorTools:
    """代码重构工具类，提供代码分析和重构建议"""

    # 代码异味检测阈值配置
    LONG_FUNCTION_LINES = 30  # 长函数阈值（行数）
    DEEP_NESTING_LEVEL = 4  # 深度嵌套阈值（层级）
    MAX_FUNCTION_PARAMS = 5  # 函数参数过多阈值
    DUPLICATE_LINE_THRESHOLD = 5  # 重复代码检测阈值
    MAX_CLASS_METHODS = 15  # 类方法过多阈值
    LONG_CLASS_LINES = 200  # 长类阈值（行数）

    def __init__(self, source_code: str = None, file_path: str = None, llm_client: SimpleLLMClient = None):
        """
        初始化重构工具

        Args:
            source_code: Python源代码字符串
            file_path: Python文件路径
            llm_client: LLM客户端实例，如果不提供则自动创建
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
        self.llm_client = llm_client or SimpleLLMClient()

    @tool
    def check_code_smells(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        检测代码异味

        检测以下类型的代码异味：
        - 长函数（Long Function）：函数行数过多
        - 深度嵌套（Deep Nesting）：if/for/while嵌套层级过深
        - 参数过多（Long Parameter List）：函数参数数量过多
        - 重复代码（Duplicate Code）：相似代码片段
        - 大类（Large Class）：类行数或方法数过多
        - 数据类（Data Class）：仅包含数据的类
        - 特质依恋（Feature Envy）：方法过多使用其他类

        Returns:
            包含各类代码异味的字典
        """
        smells = {
            'long_functions': self._check_long_functions(),
            'deep_nesting': self._check_deep_nesting(),
            'long_parameter_list': self._check_long_parameter_list(),
            'duplicate_code': self._check_duplicate_code(),
            'large_classes': self._check_large_classes(),
            'data_classes': self._check_data_classes(),
            'feature_envy': self._check_feature_envy()
        }

        # 移除空列表
        return {k: v for k, v in smells.items() if v}

    def _check_long_functions(self) -> List[Dict[str, Any]]:
        """检测长函数"""
        long_functions = []

        for node in ast.walk(self.tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # 计算函数行数
                func_start = node.lineno
                func_end = node.end_lineno if hasattr(node, 'end_lineno') else func_start
                func_lines = func_end - func_start + 1

                if func_lines > self.LONG_FUNCTION_LINES:
                    long_functions.append({
                        'name': node.name,
                        'line_number': func_start,
                        'lines': func_lines,
                        'severity': 'high' if func_lines > 50 else 'medium',
                        'description': f'函数 "{node.name}" 过长 ({func_lines} 行)，建议拆分为更小的函数'
                    })

        return long_functions

    def _check_deep_nesting(self) -> List[Dict[str, Any]]:
        """检测深度嵌套"""
        deep_nesting = []

        for node in ast.walk(self.tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                nesting_info = self._get_max_nesting(node, node)
                if nesting_info['max_level'] > self.DEEP_NESTING_LEVEL:
                    deep_nesting.append({
                        'function': node.name,
                        'line_number': node.lineno,
                        'max_nesting_level': nesting_info['max_level'],
                        'problematic_line': nesting_info['line'],
                        'severity': 'high' if nesting_info['max_level'] > 5 else 'medium',
                        'description': f'函数 "{node.name}" 存在 {nesting_info["max_level"]} 层嵌套，建议使用卫语句或提取方法'
                    })

        return deep_nesting

    def _get_max_nesting(self, node: ast.AST, root_node: ast.AST, level: int = 0) -> Dict[str, int]:
        """递归计算最大嵌套层级"""
        max_level = level
        problematic_line = node.lineno if hasattr(node, 'lineno') else 0

        for child in ast.walk(node):
            # 只遍历当前节点的直接子节点
            if child not in ast.walk(node):
                continue

            if isinstance(child, (ast.If, ast.While, ast.For, ast.With, ast.Try)):
                # 检查是否在当前函数的直接作用域内
                for body_item in ast.iter_child_nodes(child):
                    result = self._get_max_nesting(body_item, root_node, level + 1)
                    if result['max_level'] > max_level:
                        max_level = result['max_level']
                        problematic_line = result['line']

        return {'max_level': max_level, 'line': problematic_line}

    def _check_long_parameter_list(self) -> List[Dict[str, Any]]:
        """检测参数过多的函数"""
        long_params = []

        for node in ast.walk(self.tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                arg_count = len(node.args.args)
                # 排除self参数
                if arg_count > 0 and node.args.args[0].arg == 'self':
                    arg_count -= 1

                if arg_count > self.MAX_FUNCTION_PARAMS:
                    long_params.append({
                        'name': node.name,
                        'line_number': node.lineno,
                        'parameter_count': arg_count,
                        'parameters': [arg.arg for arg in node.args.args],
                        'severity': 'medium',
                        'description': f'函数 "{node.name}" 有 {arg_count} 个参数，考虑使用参数对象'
                    })

        return long_params

    def _check_duplicate_code(self) -> List[Dict[str, Any]]:
        """检测重复代码（简化版本，基于AST节点相似度）"""
        duplicates = []
        functions = []

        # 收集所有函数
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(node)

        # 简单的行级重复检测
        line_groups = {}
        for i, line in enumerate(self.lines):
            stripped = line.strip()
            if stripped and not stripped.startswith('#') and len(stripped) > 20:
                if stripped not in line_groups:
                    line_groups[stripped] = []
                line_groups[stripped].append(i + 1)

        # 检测重复的代码块（连续多行）
        for line_content, line_numbers in line_groups.items():
            if len(line_numbers) >= self.DUPLICATE_LINE_THRESHOLD:
                duplicates.append({
                    'type': 'duplicate_line',
                    'content': line_content[:50] + '...' if len(line_content) > 50 else line_content,
                    'occurrences': len(line_numbers),
                    'lines': line_numbers[:5],  # 只显示前5个位置
                    'severity': 'low',
                    'description': f'发现 {len(line_numbers)} 处相同代码行，考虑提取为函数或常量'
                })

        return duplicates

    def _check_large_classes(self) -> List[Dict[str, Any]]:
        """检测大类"""
        large_classes = []

        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef):
                # 计算类行数
                class_start = node.lineno
                class_end = node.end_lineno if hasattr(node, 'end_lineno') else class_start
                class_lines = class_end - class_start + 1

                # 统计方法数量
                methods_count = sum(1 for item in node.body if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)))

                is_large = class_lines > self.LONG_CLASS_LINES or methods_count > self.MAX_CLASS_METHODS

                if is_large:
                    large_classes.append({
                        'name': node.name,
                        'line_number': class_start,
                        'lines': class_lines,
                        'methods_count': methods_count,
                        'severity': 'high' if methods_count > 20 else 'medium',
                        'description': f'类 "{node.name}" 过大（{methods_count} 个方法，{class_lines} 行），建议拆分职责'
                    })

        return large_classes

    def _check_data_classes(self) -> List[Dict[str, Any]]:
        """检测数据类（仅包含数据的类，缺少行为）"""
        data_classes = []

        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef):
                # 统计方法和属性
                methods = []
                attributes = []

                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        # 跳过魔术方法
                        if not item.name.startswith('__'):
                            methods.append(item.name)
                    elif isinstance(item, ast.AnnAssign) or isinstance(item, ast.Assign):
                        if isinstance(item, ast.AnnAssign):
                            if isinstance(item.target, ast.Name):
                                attributes.append(item.target.id)
                        elif isinstance(item.targets[0], ast.Name):
                            attributes.append(item.targets[0].id)

                # 如果几乎没有方法但有属性，可能是数据类
                if len(methods) <= 1 and len(attributes) >= 2:
                    data_classes.append({
                        'name': node.name,
                        'line_number': node.lineno,
                        'attributes': attributes,
                        'methods': methods,
                        'severity': 'info',
                        'description': f'类 "{node.name}" 可能是数据类，考虑使用 dataclass 或添加行为方法'
                    })

        return data_classes

    def _check_feature_envy(self) -> List[Dict[str, Any]]:
        """检测特质依恋（方法过多使用其他类）"""
        feature_envy = []

        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        # 检查方法中的属性访问
                        external_access_count = 0
                        self_access_count = 0

                        for child in ast.walk(item):
                            if isinstance(child, ast.Attribute):
                                # 检查是否访问self的属性
                                if isinstance(child.value, ast.Name) and child.value.id == 'self':
                                    self_access_count += 1
                                else:
                                    external_access_count += 1

                        # 如果外部访问远大于self访问，可能存在特质依恋
                        if external_access_count > 3 and external_access_count > self_access_count * 2:
                            feature_envy.append({
                                'class': node.name,
                                'method': item.name,
                                'line_number': item.lineno,
                                'self_access': self_access_count,
                                'external_access': external_access_count,
                                'severity': 'low',
                                'description': f'方法 "{item.name}" 可能应该移到它频繁使用的类中'
                            })

        return feature_envy

    @tool
    def suggest_refactoring(self, focus_area: Optional[str] = None) -> Dict[str, Any]:
        """
        分析代码并给出重构建议

        Args:
            focus_area: 可选的聚焦区域，如 'functions', 'classes', 'general'

        Returns:
            包含重构建议的字典
        """
        # 首先检测代码异味
        code_smells = self.check_code_smells()

        # 构建提示词
        prompt = self._build_refactor_prompt(code_smells, focus_area)

        # 使用LLM生成重构建议
        try:
            llm_response = self.llm_client.generate(
                prompt,
                temperature=0.3,
                max_tokens=2000
            )

            # 解析LLM响应
            suggestions = self._parse_llm_suggestions(llm_response)

            return {
                'code_smells': code_smells,
                'ai_suggestions': suggestions,
                'summary': self._generate_summary(code_smells, suggestions)
            }
        except Exception as e:
            return {
                'code_smells': code_smells,
                'error': f'获取AI建议失败: {str(e)}',
                'summary': f'检测到 {sum(len(v) for v in code_smells.values())} 个代码异味'
            }

    def _build_refactor_prompt(self, code_smells: Dict, focus_area: Optional[str]) -> str:
        """构建重构分析的提示词"""
        prompt = f"""作为代码重构专家，请分析以下Python代码并提供重构建议。

代码预览（前500字符）:
{self.source_code[:500]}

检测到的代码异味:
"""

        for smell_type, issues in code_smells.items():
            prompt += f"\n{smell_type}:\n"
            for issue in issues[:3]:  # 限制每个类型最多3个
                prompt += f"  - {issue.get('description', 'N/A')}\n"

        if focus_area:
            prompt += f"\n请重点关注: {focus_area}\n"

        prompt += """
请提供具体的重构建议，格式如下：
1. 优先级（高/中/低）
2. 具体问题说明
3. 建议的重构方法
4. 重构后的预期效果

每条建议用 "---" 分隔。"""
        return prompt

    def _parse_llm_suggestions(self, llm_response: str) -> List[Dict[str, str]]:
        """解析LLM返回的建议"""
        suggestions = []
        parts = llm_response.split('---')

        for part in parts:
            part = part.strip()
            if not part:
                continue

            # 尝试解析结构化建议
            suggestion = {
                'raw': part,
                'priority': 'medium',
                'description': part[:200]
            }

            # 检测优先级关键词
            if any(word in part for word in ['高', 'high', '紧急', 'important']):
                suggestion['priority'] = 'high'
            elif any(word in part for word in ['低', 'low', '可选', 'optional']):
                suggestion['priority'] = 'low'

            suggestions.append(suggestion)

        return suggestions

    def _generate_summary(self, code_smells: Dict, suggestions: List[Dict]) -> str:
        """生成重构建议摘要"""
        total_issues = sum(len(v) for v in code_smells.values())
        high_priority = sum(1 for s in suggestions if s.get('priority') == 'high')

        if total_issues == 0:
            return "未检测到明显的代码异味，代码质量良好。"

        return f"检测到 {total_issues} 个代码异味，其中 {high_priority} 个高优先级问题需要处理。"

    @tool
    def apply_refactoring(self, description: str, target: Optional[str] = None) -> Dict[str, Any]:
        """
        根据描述应用重构（生成重构代码，不直接修改原文件）

        Args:
            description: 重构操作的描述，如 "提取函数calculate_sum中的重复逻辑"
            target: 可选的目标函数或类名

        Returns:
            包含重构结果的字典
        """
        # 构建提示词
        prompt = f"""请根据以下描述对代码进行重构：

重构描述: {description}
"""
        if target:
            prompt += f"目标: {target}\n"

        prompt += f"""
原始代码:
```
{self.source_code}
```

请提供:
1. 重构后的完整代码
2. 重构说明（改动内容和原因）

只返回代码和说明，不要包含其他内容。"""

        try:
            response = self.llm_client.generate(
                prompt,
                temperature=0.2,
                max_tokens=3000
            )

            # 尝试提取代码块
            refactored_code = self._extract_code_from_response(response)
            explanation = self._extract_explanation_from_response(response)

            return {
                'success': True,
                'original_code': self.source_code,
                'refactored_code': refactored_code,
                'explanation': explanation,
                'description': description,
                'target': target
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'description': description
            }

    def _extract_code_from_response(self, response: str) -> Optional[str]:
        """从LLM响应中提取代码块"""
        # 尝试提取markdown代码块
        code_pattern = r'```python\n(.*?)```'
        match = re.search(code_pattern, response, re.DOTALL)
        if match:
            return match.group(1).strip()

        # 尝试提取普通代码块
        code_pattern = r'```\n(.*?)```'
        match = re.search(code_pattern, response, re.DOTALL)
        if match:
            return match.group(1).strip()

        return None

    def _extract_explanation_from_response(self, response: str) -> str:
        """从LLM响应中提取说明"""
        # 移除代码块
        response = re.sub(r'```.*?```', '', response, flags=re.DOTALL)
        return response.strip()

    @tool
    def get_refactoring_priority(self) -> List[Dict[str, Any]]:
        """
        获取重构优先级建议

        Returns:
            按优先级排序的重构任务列表
        """
        code_smells = self.check_code_smells()

        priority_items = []

        # 为每个代码异味分配分数
        for smell_type, issues in code_smells.items():
            for issue in issues:
                score = self._calculate_issue_score(smell_type, issue)
                priority_items.append({
                    'type': smell_type,
                    'issue': issue,
                    'score': score,
                    'priority': self._score_to_priority(score)
                })

        # 按分数排序
        priority_items.sort(key=lambda x: x['score'], reverse=True)

        return priority_items

    def _calculate_issue_score(self, smell_type: str, issue: Dict) -> int:
        """计算问题严重程度分数"""
        base_scores = {
            'long_functions': 10,
            'deep_nesting': 15,
            'long_parameter_list': 5,
            'duplicate_code': 8,
            'large_classes': 12,
            'data_classes': 3,
            'feature_envy': 4
        }

        base = base_scores.get(smell_type, 5)

        # 根据严重程度调整
        severity_multiplier = {
            'high': 2.0,
            'very_high': 2.5,
            'medium': 1.0,
            'low': 0.5,
            'info': 0.2
        }

        severity = issue.get('severity', 'medium')
        multiplier = severity_multiplier.get(severity, 1.0)

        return int(base * multiplier)

    def _score_to_priority(self, score: int) -> str:
        """将分数转换为优先级"""
        if score >= 20:
            return 'critical'
        elif score >= 15:
            return 'high'
        elif score >= 10:
            return 'medium'
        else:
            return 'low'

    @tool
    def get_complexity_metrics(self) -> Dict[str, Any]:
        """
        获取代码复杂度指标

        Returns:
            包含各种复杂度指标的字典
        """
        metrics = {
            'total_lines': len(self.lines),
            'functions': self._count_functions(),
            'classes': self._count_classes(),
            'cyclomatic_complexity': self._calculate_cyclomatic_complexity(),
            'maintainability_index': self._calculate_maintainability_index(),
            'code_duplication': self._calculate_duplication_rate()
        }

        return metrics

    def _count_functions(self) -> Dict[str, int]:
        """统计函数数量"""
        total = 0
        async_funcs = 0

        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                total += 1
            elif isinstance(node, ast.AsyncFunctionDef):
                total += 1
                async_funcs += 1

        return {
            'total': total,
            'async': async_funcs,
            'sync': total - async_funcs
        }

    def _count_classes(self) -> Dict[str, int]:
        """统计类数量"""
        count = 0
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef):
                count += 1

        return {'total': count}

    def _calculate_cyclomatic_complexity(self) -> Dict[str, Any]:
        """计算圈复杂度"""
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
            'value': complexity,
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

    def _calculate_maintainability_index(self) -> float:
        """计算可维护性指数（简化版本）"""
        # MI = MAX(0, (171 - 5.2 * ln(HV) - 0.23 * CC - 16.2 * ln(LOC)) * 100 / 171)
        # 这里使用简化版本

        # 获取指标
        lines = len(self.lines)
        cc = self._calculate_cyclomatic_complexity()['value']
        functions = self._count_functions()['total']

        if functions == 0:
            functions = 1

        # 简化的计算
        volume = lines * (1 + 0.1 * cc)
        mi = max(0, 100 - (volume / lines) * 10 - cc * 2)

        return round(mi, 2)

    def _calculate_duplication_rate(self) -> Dict[str, Any]:
        """计算代码重复率"""
        total_lines = len(self.lines)
        duplicate_lines = 0

        # 统计重复行
        line_counts = {}
        for line in self.lines:
            stripped = line.strip()
            if stripped and not stripped.startswith('#') and len(stripped) > 15:
                line_counts[stripped] = line_counts.get(stripped, 0) + 1

        for count in line_counts.values():
            if count > 1:
                duplicate_lines += count - 1

        rate = (duplicate_lines / total_lines * 100) if total_lines > 0 else 0

        return {
            'duplicate_lines': duplicate_lines,
            'total_lines': total_lines,
            'rate_percentage': round(rate, 2)
        }
