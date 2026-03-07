"""ReAct Agent - 基于推理+行动循环的代码助手Agent"""

import json
import re
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
import sys

# 从项目内模块导入
sys.path.insert(0, str(Path(__file__).parent.parent))
from llm_client import SimpleLLMClient
from embeddings import EmbeddingModel
from vector_store import VectorStore
from document_loader import Document

# 导入工具
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
from code_analyzer import CodeAnalyzer


class ToolRegistry:
    """工具注册表，管理所有可用工具"""

    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._tool_descriptions: Dict[str, str] = {}

    def register(self, name: str, func: Callable, description: str):
        """注册工具"""
        self._tools[name] = func
        self._tool_descriptions[name] = description

    def get(self, name: str) -> Optional[Callable]:
        """获取工具"""
        return self._tools.get(name)

    def get_description(self, name: str) -> Optional[str]:
        """获取工具描述"""
        return self._tool_descriptions.get(name)

    def list_tools(self) -> List[str]:
        """列出所有工具名称"""
        return list(self._tools.keys())

    def get_all_descriptions(self) -> Dict[str, str]:
        """获取所有工具描述"""
        return self._tool_descriptions.copy()


class ReActAgent:
    """
    ReAct Agent - 实现 Reasoning + Acting 循环

    思路：
    1. Thought: LLM分析问题，决定下一步行动
    2. Action: 选择并执行工具
    3. Observation: 获取工具执行结果
    4. 重复直到找到答案或达到最大迭代次数
    """

    # ReAct提示词模板
    REACT_PROMPT_TEMPLATE = """你是一个代码助手Agent，可以帮助分析代码结构、统计代码行数、分析类和函数等。

可用工具：
{tool_descriptions}

请遵循以下格式进行思考和行动：

Thought: 你的思考过程，分析当前情况
Action: 工具名称 (必须是上述可用工具之一)
Action Input: 工具输入参数（JSON格式）
Observation: 工具执行结果
... (可以重复 Thought-Action-Observation 多次)
Thought: 我现在知道最终答案了
Final Answer: 最终答案

开始！

用户问题：{query}

{history}

Thought:"""

    MAX_ITERATIONS = 10  # 最大迭代次数

    def __init__(
        self,
        llm_client: Optional[SimpleLLMClient] = None,
        enable_memory: bool = False
    ):
        """
        初始化ReAct Agent

        Args:
            llm_client: LLM客户端（如不提供则创建新实例）
            enable_memory: 是否启用记忆功能（使用向量存储）
        """
        # 初始化LLM客户端
        self.llm_client = llm_client or SimpleLLMClient()

        # 初始化工具注册表
        self.tool_registry = ToolRegistry()
        self._register_tools()

        # 初始化记忆（可选）
        self.enable_memory = enable_memory
        if enable_memory:
            self.embedding_model = EmbeddingModel()
            self.vector_store = VectorStore(
                collection_name="agent_memory",
                persist_directory="./project3-code-agent/data/memory"
            )

        # 当前会话的代码分析器缓存
        self._code_analyzer_cache: Dict[str, CodeAnalyzer] = {}

    def _register_tools(self):
        """注册所有可用工具"""

        # 1. analyze_code - 分析代码文件
        def analyze_code(file_path: str) -> Dict[str, Any]:
            """分析Python代码文件"""
            if file_path not in self._code_analyzer_cache:
                try:
                    self._code_analyzer_cache[file_path] = CodeAnalyzer(file_path=file_path)
                except Exception as e:
                    return {"error": str(e)}
            analyzer = self._code_analyzer_cache[file_path]
            return analyzer.get_full_report()

        self.tool_registry.register(
            "analyze_code",
            analyze_code,
            "分析Python代码文件，获取完整的代码结构报告。输入: file_path (字符串)"
        )

        # 2. list_functions - 列出函数
        def list_functions(file_path: str) -> List[Dict[str, Any]]:
            """列出代码中的所有函数"""
            if file_path not in self._code_analyzer_cache:
                try:
                    self._code_analyzer_cache[file_path] = CodeAnalyzer(file_path=file_path)
                except Exception as e:
                    return [{"error": str(e)}]
            analyzer = self._code_analyzer_cache[file_path]
            return analyzer.analyze_functions()

        self.tool_registry.register(
            "list_functions",
            list_functions,
            "列出代码文件中的所有函数。输入: file_path (字符串)"
        )

        # 3. list_classes - 列出类
        def list_classes(file_path: str) -> List[Dict[str, Any]]:
            """列出代码中的所有类"""
            if file_path not in self._code_analyzer_cache:
                try:
                    self._code_analyzer_cache[file_path] = CodeAnalyzer(file_path=file_path)
                except Exception as e:
                    return [{"error": str(e)}]
            analyzer = self._code_analyzer_cache[file_path]
            return analyzer.analyze_classes()

        self.tool_registry.register(
            "list_classes",
            list_classes,
            "列出代码文件中的所有类。输入: file_path (字符串)"
        )

        # 4. count_lines - 统计行数
        def count_lines(file_path: str) -> Dict[str, int]:
            """统计代码行数"""
            if file_path not in self._code_analyzer_cache:
                try:
                    self._code_analyzer_cache[file_path] = CodeAnalyzer(file_path=file_path)
                except Exception as e:
                    return {"error": str(e)}
            analyzer = self._code_analyzer_cache[file_path]
            return analyzer.count_lines()

        self.tool_registry.register(
            "count_lines",
            count_lines,
            "统计代码文件的行数（总行数、代码行、注释行等）。输入: file_path (字符串)"
        )

        # 5. get_imports - 获取导入
        def get_imports(file_path: str) -> Dict[str, List[Dict]]:
            """获取所有import语句"""
            if file_path not in self._code_analyzer_cache:
                try:
                    self._code_analyzer_cache[file_path] = CodeAnalyzer(file_path=file_path)
                except Exception as e:
                    return {"error": str(e)}
            analyzer = self._code_analyzer_cache[file_path]
            return analyzer.get_imports()

        self.tool_registry.register(
            "get_imports",
            get_imports,
            "获取代码文件中的所有import语句。输入: file_path (字符串)"
        )

        # 6. get_complexity - 获取复杂度
        def get_complexity(file_path: str) -> Dict[str, Any]:
            """获取代码复杂度"""
            if file_path not in self._code_analyzer_cache:
                try:
                    self._code_analyzer_cache[file_path] = CodeAnalyzer(file_path=file_path)
                except Exception as e:
                    return {"error": str(e)}
            analyzer = self._code_analyzer_cache[file_path]
            return analyzer.get_complexity()

        self.tool_registry.register(
            "get_complexity",
            get_complexity,
            "计算代码的圈复杂度。输入: file_path (字符串)"
        )

        # 7. read_file - 读取文件
        def read_file(file_path: str) -> str:
            """读取文件内容"""
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                # 限制长度
                if len(content) > 5000:
                    content = content[:5000] + "\n... (内容过长，已截断)"
                return content
            except Exception as e:
                return f"读取文件失败: {e}"

        self.tool_registry.register(
            "read_file",
            read_file,
            "读取文件内容。输入: file_path (字符串)"
        )

    def run(self, query: str, verbose: bool = True) -> str:
        """
        执行ReAct循环

        Args:
            query: 用户查询
            verbose: 是否打印详细过程

        Returns:
            最终答案
        """
        # 准备工具描述
        tool_descriptions = "\n".join([
            f"- {name}: {desc}"
            for name, desc in self.tool_registry.get_all_descriptions().items()
        ])

        # 历史记录
        history = ""

        # 执行ReAct循环
        for iteration in range(self.MAX_ITERATIONS):
            if verbose:
                print(f"\n{'='*60}")
                print(f"迭代 {iteration + 1}/{self.MAX_ITERATIONS}")
                print(f"{'='*60}")

            # 构建提示词
            prompt = self.REACT_PROMPT_TEMPLATE.format(
                tool_descriptions=tool_descriptions,
                query=query,
                history=history
            )

            if verbose:
                print(f"\n{'─'*60}")
                print("【发送给 LLM 的提示词】")
                print(f"{'─'*60}")
                print(prompt)
                print(f"{'─'*60}")

            # 获取LLM响应
            response = self.llm_client.generate(prompt, temperature=0.3)

            if verbose:
                print(f"\n{'─'*60}")
                print("【LLM 返回的响应】")
                print(f"{'─'*60}")
                print(response)
                print(f"{'─'*60}")

            # 解析响应
            thought, action, action_input, final_answer = self._parse_response(response)

            if verbose:
                print(f"\n{'─'*60}")
                print("【解析结果】")
                print(f"{'─'*60}")
                print(f"Thought: {thought}")
                print(f"Action: {action}")
                print(f"Action Input: {action_input}")
                print(f"Final Answer: {final_answer}")
                print(f"{'─'*60}")

            # 检查是否有最终答案
            if final_answer:
                if verbose:
                    print(f"\n最终答案: {final_answer}")

                # 保存到记忆
                if self.enable_memory:
                    self._save_to_memory(query, final_answer)

                return final_answer

            # 执行行动
            if action and action_input:
                if verbose:
                    print(f"\n执行: {action}")
                    print(f"参数: {action_input}")

                observation = self._execute_action(action, action_input)

                if verbose:
                    print(f"结果: {observation}\n")

                # 添加到历史
                history += f"\nThought: {thought}\n"
                history += f"Action: {action}\n"
                history += f"Action Input: {action_input}\n"
                history += f"Observation: {observation}\n"
            else:
                # 无法解析响应，要求重新思考
                history += f"\n响应无法理解，请重新思考并按照正确格式回答。\n"

        return "达到最大迭代次数，未能找到答案。"

    def _parse_response(self, response: str) -> tuple:
        """
        解析LLM响应

        Returns:
            (thought, action, action_input, final_answer)
        """
        thought = None
        action = None
        action_input = None
        final_answer = None

        # 尝试提取Final Answer
        final_match = re.search(r'Final Answer:\s*(.+?)(?:\n|$)', response, re.IGNORECASE)
        if final_match:
            final_answer = final_match.group(1).strip()
            return thought, action, action_input, final_answer

        # 提取Thought
        thought_match = re.search(r'Thought:\s*(.+?)(?:\n|$)', response, re.IGNORECASE)
        if thought_match:
            thought = thought_match.group(1).strip()

        # 提取Action
        action_match = re.search(r'Action:\s*(.+?)(?:\n|$)', response, re.IGNORECASE)
        if action_match:
            action = action_match.group(1).strip()

        # 提取Action Input
        action_input_match = re.search(r'Action Input:\s*(.+?)(?=\n(?:Thought|Action|Final Answer)|$)', response, re.IGNORECASE | re.DOTALL)
        if action_input_match:
            action_input_str = action_input_match.group(1).strip()
            # 尝试解析JSON
            try:
                action_input = json.loads(action_input_str)
            except json.JSONDecodeError:
                # 如果不是JSON，尝试提取值
                if ':' in action_input_str:
                    key, value = action_input_str.split(':', 1)
                    action_input = {key.strip(): value.strip()}
                else:
                    action_input = action_input_str

        return thought, action, action_input, final_answer

    def _execute_action(self, action: str, action_input: Any) -> str:
        """
        执行工具行动

        Args:
            action: 工具名称
            action_input: 工具输入

        Returns:
            执行结果字符串
        """
        tool = self.tool_registry.get(action)

        if tool is None:
            return f"错误: 未找到工具 '{action}'"

        try:
            # 处理不同类型的输入
            if isinstance(action_input, str):
                result = tool(action_input)
            elif isinstance(action_input, dict):
                # 如果只有一个key，取其值作为参数
                if len(action_input) == 1:
                    result = tool(list(action_input.values())[0])
                else:
                    result = tool(**action_input)
            else:
                result = tool(action_input)

            # 转换结果为字符串
            if isinstance(result, dict):
                return json.dumps(result, ensure_ascii=False, indent=2)
            elif isinstance(result, list):
                return json.dumps(result, ensure_ascii=False, indent=2)
            else:
                return str(result)

        except Exception as e:
            return f"执行错误: {str(e)}"

    def _save_to_memory(self, query: str, answer: str):
        """保存对话到记忆"""
        doc = Document(
            page_content=f"问题: {query}\n答案: {answer}",
            metadata={"type": "qa_pair"}
        )
        self.vector_store.add_documents([doc], self.embedding_model)

    def recall(self, query: str, k: int = 3) -> List[str]:
        """从记忆中召回相关内容"""
        if not self.enable_memory:
            return []

        results = self.vector_store.search(query, self.embedding_model, k=k)
        return [doc.page_content for doc in results]


# 别名，便于使用
CodeAssistantAgent = ReActAgent
