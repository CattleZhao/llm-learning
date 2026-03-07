"""
LangChain 版本的代码分析 Agent

使用 LangChain 的 create_react_agent 和 AgentExecutor
"""
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from llm_client import create_llm
from tools.langchain_tools import get_all_tools
from tools.code_analyzer import CodeAnalyzer
from memory.conversation_memory import ConversationMemory
from memory.project_memory import ProjectMemory


class LangChainCodeAgent:
    """
    使用 LangChain 实现的代码分析 Agent
    """

    def __init__(self, workspace_dir: str = None):
        """
        初始化 Agent

        Args:
            workspace_dir: 工作目录路径
        """
        # 初始化 LLM
        self.llm = create_llm(temperature=0.3)

        # 创建工具列表
        self.tools = get_all_tools()

        # 创建 Agent
        from langchain.agents import create_react_agent
        from langchain import hub

        # 获取标准 ReAct prompt 模板
        self.prompt = hub.pull("hwchase17/react")

        # 创建 ReAct Agent
        self.agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )

        # 创建 Agent 执行器
        from langchain.agents import AgentExecutor

        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            max_iterations=10,
            handle_parsing_errors=True,
            return_intermediate_steps=False
        )

        # 记忆（用于非 Agent 模式的功能）
        self.conversation_memory = ConversationMemory()
        self.project_memory = ProjectMemory(workspace_dir)
        self.current_file = None

        # 系统提示词（用于直接调用模式）
        self.system_prompt = """你是一个专业的代码分析助手，具备以下能力：

1. 代码结构分析 - 分析函数、类、导入等代码结构
2. 代码质量评估 - 评估复杂度、可读性等
3. 测试用例生成 - 为函数自动生成测试代码
4. 重构建议 - 提供代码改进建议

请使用工具获取信息后，给出清晰、有价值的分析结果。"""

    def chat(self, user_input: str) -> str:
        """
        通过 Agent 处理用户输入

        Args:
            user_input: 用户输入

        Returns:
            Agent 回复
        """
        try:
            result = self.agent_executor.invoke({"input": user_input})
            return result.get("output", "未能获取回复")
        except Exception as e:
            return f"执行出错: {str(e)}"

    def analyze_code(self, file_path: str = None, source_code: str = None) -> Dict[str, Any]:
        """
        分析代码（直接调用，不使用 Agent）

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

        report = analyzer.get_full_report()

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
        analysis = self.analyze_code(file_path=file_path)
        functions = analysis.get("functions", [])

        if function_name:
            func_info = next((f for f in functions if f["name"] == function_name), None)
            if not func_info:
                return f"未找到函数: {function_name}"
            prompt = f"为以下函数生成完整的单元测试代码（使用pytest）:\n\n函数名: {func_info['name']}\n参数数量: {func_info['args_count']}"
        else:
            func_list = "\n".join([f"- {f['name']}" for f in functions])
            prompt = f"为以下所有函数生成完整的单元测试代码（使用pytest）:\n\n{func_list}"

        from langchain.schema import HumanMessage
        result = self.llm.invoke([HumanMessage(content=prompt)])

        self.project_memory.add_analysis_history("test_generation", file_path, {"response": result.content})

        return result.content

    def suggest_refactor(self, file_path: str) -> str:
        """
        提供重构建议

        Args:
            file_path: 文件路径

        Returns:
            重构建议
        """
        analysis = self.analyze_code(file_path=file_path)

        prompt = f"""基于以下代码分析结果，提供详细的重构建议：

代码统计: {analysis.get('lines', {})}
复杂度: {analysis.get('complexity', {})}
函数: {analysis.get('functions', [])}
类: {analysis.get('classes', [])}

请针对以下方面提供建议：
1. 复杂度过高的函数
2. 可以改进的代码结构
3. 潜在的设计模式应用
4. 性能优化建议
5. 可读性改进建议"""

        from langchain.schema import HumanMessage
        result = self.llm.invoke([HumanMessage(content=prompt)])

        self.project_memory.add_analysis_history("refactor_suggestion", file_path, {"response": result.content})

        return result.content

    def evaluate_quality(self, file_path: str) -> Dict[str, Any]:
        """
        评估代码质量

        Args:
            file_path: 文件路径

        Returns:
            质量评估结果
        """
        analysis = self.analyze_code(file_path=file_path)

        complexity = analysis.get('complexity', {})
        lines = analysis.get('lines', {})
        functions = analysis.get('functions', [])

        score = 100
        issues = []

        if complexity.get('cyclomatic_complexity', 0) > 20:
            score -= 20
            issues.append("复杂度过高，建议拆分函数")
        elif complexity.get('cyclomatic_complexity', 0) > 10:
            score -= 10
            issues.append("复杂度较高")

        for func in functions:
            if isinstance(func, dict) and func.get('args_count', 0) > 5:
                score -= 5
                issues.append(f"函数 {func.get('name')} 参数过多")

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
