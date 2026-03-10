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
        from langchain.agents import create_react_agent, AgentExecutor
        from langchain_core.prompts import PromptTemplate

        # 定义 ReAct prompt 模板（不依赖 hub）
        REACT_TEMPLATE = """Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:{agent_scratchpad}"""

        self.prompt = PromptTemplate.from_template(REACT_TEMPLATE)

        # 创建 ReAct Agent
        self.agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )

        # 创建 LangChain 记忆组件
        from langchain.memory import ConversationBufferMemory

        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )

        # 创建 Agent 执行器（带记忆）
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            max_iterations=10,
            handle_parsing_errors=True,
            return_intermediate_steps=False,
            memory=self.memory  # 关键：传入记忆组件
        )

        # 对话历史记录（手动管理）
        self.chat_history = []  # 存储 {"role": "user"/"assistant", "content": "..."}

    def chat(self, user_input: str) -> str:
        """
        通过 Agent 处理用户输入（支持多轮对话）

        Args:
            user_input: 用户输入

        Returns:
            Agent 回复
        """
        try:
            # 构建包含历史对话的输入
            if self.chat_history:
                # 如果有历史记录，添加到输入中
                history_text = "\n\n".join([
                    f"{msg['role']}: {msg['content']}"
                    for msg in self.chat_history[-4:]  # 只保留最近4轮
                ])
                full_input = f"之前的对话:\n{history_text}\n\n当前问题: {user_input}"
            else:
                full_input = user_input

            result = self.agent_executor.invoke({"input": full_input})
            response = result.get("output", "未能获取回复")

            # 记录到历史
            self.chat_history.append({"role": "user", "content": user_input})
            self.chat_history.append({"role": "assistant", "content": response})

            return response
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
        self.chat_history = []
        self.conversation_memory.clear()
        self.conversation_memory.add_system_message(self.system_prompt)
