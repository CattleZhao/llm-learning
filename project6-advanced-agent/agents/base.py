"""
Agent 基类模块

定义所有 Agent 的基础接口和通用功能
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class AgentResponse:
    """Agent 响应"""
    content: str                          # 响应内容
    tool_calls: List[Dict] = field(default_factory=list)  # 工具调用记录
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    reflection: Optional[str] = None       # 自我反思结果（如果启用）


@dataclass
class AgentState:
    """Agent 状态"""
    conversation_history: List[Dict] = field(default_factory=list)
    current_context: Dict[str, Any] = field(default_factory=dict)
    tool_results: List[Dict] = field(default_factory=list)
    iteration_count: int = 0


class BaseAgent(ABC):
    """
    Agent 基类

    所有 Agent 都应该继承此类并实现核心方法
    """

    def __init__(
        self,
        name: str,
        description: str,
        role: str = "assistant",
        enable_memory: bool = True,
        enable_reflection: bool = False
    ):
        """
        初始化 Agent

        Args:
            name: Agent 名称
            description: Agent 描述
            role: Agent 角色
            enable_memory: 是否启用记忆
            enable_reflection: 是否启用自我反思
        """
        self.name = name
        self.description = description
        self.role = role
        self.enable_memory = enable_memory
        self.enable_reflection = enable_reflection
        self.state = AgentState()

    @abstractmethod
    def think(self, input_text: str, context: Optional[Dict] = None) -> AgentResponse:
        """
        Agent 核心思考方法

        Args:
            input_text: 用户输入
            context: 额外上下文信息

        Returns:
            AgentResponse 对象
        """
        pass

    def execute(self, input_text: str, context: Optional[Dict] = None) -> AgentResponse:
        """
        执行 Agent 逻辑

        这是主要的入口方法，封装了完整的执行流程：
        1. 更新上下文
        2. 执行思考
        3. 保存记忆（如果启用）
        4. 自我反思（如果启用）

        Args:
            input_text: 用户输入
            context: 额外上下文

        Returns:
            AgentResponse 对象
        """
        # 更新状态
        self.state.iteration_count += 1
        if context:
            self.state.current_context.update(context)

        # 执行思考
        response = self.think(input_text, context)

        # 保存到历史记录
        self._save_to_history(input_text, response)

        return response

    def _save_to_history(self, input_text: str, response: AgentResponse):
        """保存对话历史"""
        self.state.conversation_history.append({
            "role": "user",
            "content": input_text,
            "timestamp": response.timestamp
        })
        self.state.conversation_history.append({
            "role": "assistant",
            "content": response.content,
            "timestamp": response.timestamp,
            "tool_calls": response.tool_calls
        })

    def get_history(self, limit: Optional[int] = None) -> List[Dict]:
        """
        获取对话历史

        Args:
            limit: 返回的最近 N 条记录，None 表示全部

        Returns:
            历史记录列表
        """
        if limit:
            return self.state.conversation_history[-limit:]
        return self.state.conversation_history

    def reset(self):
        """重置 Agent 状态"""
        self.state = AgentState()

    def __repr__(self) -> str:
        return f"Agent(name={self.name}, role={self.role})"


class ToolExecutor(ABC):
    """工具执行器基类"""

    @abstractmethod
    def execute(self, tool_name: str, **kwargs) -> Any:
        """执行工具"""
        pass

    @abstractmethod
    def list_tools(self) -> List[str]:
        """列出可用工具"""
        pass
