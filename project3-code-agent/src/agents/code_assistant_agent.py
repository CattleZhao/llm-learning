# src/agents/code_assistant_agent.py
"""
代码助手Agent - 基于ReAct框架的智能代码分析助手
"""
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..llm_client import SimpleLLMClient
from ..tools.code_analyzer import CodeAnalyzer
from ..memory.conversation_memory import ConversationMemory
from ..memory.project_memory import ProjectMemory


class CodeAssistantAgent:
    """
    代码助手Agent
    结合代码分析工具和LLM能力，提供智能代码分析服务
    """

    def __init__(self, workspace_dir: str = None):
        """
        初始化Agent

        Args:
            workspace_dir: 工作目录
        """
        self.llm_client = SimpleLLMClient()
        self.conversation_memory = ConversationMemory()
        self.project_memory = ProjectMemory(workspace_dir)
        self.current_file = None

        # 系统提示词
        self.system_prompt = """你是一个专业的代码分析助手，具备以下能力：

1. 代码结构分析 - 分析函数、类、导入等代码结构
2. 代码质量评估 - 评估复杂度、可读性等
3. 测试用例生成 - 为函数自动生成测试代码
4. 重构建议 - 提供代码改进建议

你可以使用以下工具：
- analyze_functions: 分析函数
- analyze_classes: 分析类
- count_lines: 统计代码行数
- get_imports: 获取导入语句
- get_complexity: 获取复杂度
- get_full_report: 获取完整报告

请使用工具获取信息后，给出清晰、有价值的分析结果。"""

        # 初始化时添加系统消息
        self.conversation_memory.add_system_message(self.system_prompt)

    def chat(self, user_input: str) -> str:
        """
        与用户对话

        Args:
            user_input: 用户输入

        Returns:
            Agent回复
        """
        # 添加用户消息
        self.conversation_memory.add_user_message(user_input)

        # 获取历史消息
        messages = self.conversation_memory.get_messages()

        # 调用LLM
        response = self.llm_client.chat(messages)

        # 添加助手消息
        self.conversation_memory.add_assistant_message(response)

        return response

    def analyze_code(self, file_path: str = None, source_code: str = None) -> Dict[str, Any]:
        """
        分析代码

        Args:
            file_path: 文件路径
            source_code: 源代码字符串

        Returns:
            分析结果
        """
        if file_path:
            self.current_file = file_path
            analyzer = CodeAnalyzer(file_path=file_path)
        elif source_code:
            analyzer = CodeAnalyzer(source_code=source_code)
        else:
            return {"error": "必须提供file_path或source_code"}

        # 获取完整报告
        report = analyzer.get_full_report()

        # 保存到项目记忆
        if file_path:
            self.project_memory.save_file_summary(file_path, report)

        return report

    def generate_test(self, file_path: str, function_name: str = None) -> str:
        """
        生成测试代码

        Args:
            file_path: 文件路径
            function_name: 函数名，None表示为所有函数生成

        Returns:
            测试代码
        """
        # 分析代码
        analysis = self.analyze_code(file_path=file_path)
        functions = analysis["result"]["functions"]["result"] if "result" in analysis else analysis.get("functions", [])

        # 构建提示词
        if function_name:
            func_info = next((f for f in functions if f["name"] == function_name), None)
            if not func_info:
                return f"未找到函数: {function_name}"
            prompt = f"为以下函数生成完整的单元测试代码（使用pytest）:\n\n函数名: {func_info['name']}\n参数数量: {func_info['args_count']}\n所在行: {func_info['line_number']}"
        else:
            func_list = "\n".join([f"- {f['name']} (参数: {f['args_count']}, 行: {f['line_number']})" for f in functions])
            prompt = f"为以下所有函数生成完整的单元测试代码（使用pytest）:\n\n{func_list}"

        # 调用LLM生成测试
        response = self.llm_client.generate(prompt)

        # 记录到项目记忆
        self.project_memory.add_analysis_history("test_generation", file_path, {"response": response})

        return response

    def suggest_refactor(self, file_path: str) -> str:
        """
        提供重构建议

        Args:
            file_path: 文件路径

        Returns:
            重构建议
        """
        # 分析代码
        analysis = self.analyze_code(file_path=file_path)

        # 构建提示词
        prompt = f"""基于以下代码分析结果，提供详细的重构建议：

代码统计: {analysis.get('lines', {})}
复杂度: {analysis.get('complexity', {})}
函数: {analysis.get('functions', {})}
类: {analysis.get('classes', {})}

请针对以下方面提供建议：
1. 复杂度过高的函数
2. 可以改进的代码结构
3. 潜在的设计模式应用
4. 性能优化建议
5. 可读性改进建议"""

        # 调用LLM
        response = self.llm_client.generate(prompt)

        # 记录到项目记忆
        self.project_memory.add_analysis_history("refactor_suggestion", file_path, {"response": response})

        return response

    def evaluate_quality(self, file_path: str) -> Dict[str, Any]:
        """
        评估代码质量

        Args:
            file_path: 文件路径

        Returns:
            质量评估结果
        """
        # 分析代码
        analysis = self.analyze_code(file_path=file_path)

        # 计算质量分数
        complexity = analysis.get('complexity', {}).get('result', analysis.get('complexity', {}))
        lines = analysis.get('lines', {}).get('result', analysis.get('lines', {}))
        functions = analysis.get('functions', {}).get('result', analysis.get('functions', []))

        # 简单的质量评分算法
        score = 100
        issues = []

        # 复杂度扣分
        if complexity.get('cyclomatic_complexity', 0) > 20:
            score -= 20
            issues.append("复杂度过高，建议拆分函数")
        elif complexity.get('cyclomatic_complexity', 0) > 10:
            score -= 10
            issues.append("复杂度较高")

        # 函数长度扣分
        for func in functions:
            if isinstance(func, dict) and func.get('args_count', 0) > 5:
                score -= 5
                issues.append(f"函数 {func.get('name')} 参数过多")

        # 代码行比例
        if lines:
            code_ratio = lines.get('code', 0) / max(lines.get('total', 1), 1)
            if code_ratio < 0.3:
                score -= 10
                issues.append("注释比例过高或空行过多")

        result = {
            "score": max(0, score),
            "level": "优秀" if score >= 90 else "良好" if score >= 70 else "需改进" if score >= 50 else "差",
            "issues": issues,
            "analysis": analysis
        }

        # 记录到项目记忆
        self.project_memory.add_analysis_history("quality_evaluation", file_path, result)

        return result

    def get_context(self) -> Dict[str, Any]:
        """
        获取当前上下文信息

        Returns:
            上下文字典
        """
        return {
            "conversation_summary": self.conversation_memory.get_summary(),
            "project_stats": self.project_memory.get_stats(),
            "current_file": self.current_file,
            "recent_analyses": self.project_memory.get_analysis_history(limit=5)
        }

    def clear_conversation(self):
        """清空对话历史"""
        self.conversation_memory.clear()
        self.conversation_memory.add_system_message(self.system_prompt)

    def search_history(self, keyword: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        搜索历史记录

        Args:
            keyword: 关键词

        Returns:
            搜索结果
        """
        return self.project_memory.search_memory(keyword)
