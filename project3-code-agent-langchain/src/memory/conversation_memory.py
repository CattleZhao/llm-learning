# src/memory/conversation_memory.py
"""
对话记忆模块 - 管理会话中的对话历史
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import json


class Message:
    """消息类"""

    def __init__(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """
        初始化消息

        Args:
            role: 消息角色 (user/assistant/system)
            content: 消息内容
            metadata: 可选的元数据
        """
        self.role = role
        self.content = content
        self.metadata = metadata or {}
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "role": self.role,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """从字典创建消息"""
        msg = cls(data["role"], data["content"], data.get("metadata"))
        msg.timestamp = data.get("timestamp", datetime.now().isoformat())
        return msg


class ConversationMemory:
    """
    对话记忆管理器
    管理会话中的对话历史，支持历史查询和上下文维护
    """

    def __init__(self, max_history: int = 100):
        """
        初始化对话记忆

        Args:
            max_history: 最大保存的消息数量
        """
        self.messages: List[Message] = []
        self.max_history = max_history
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """
        添加消息到记忆中

        Args:
            role: 消息角色 (user/assistant/system)
            content: 消息内容
            metadata: 可选的元数据
        """
        message = Message(role, content, metadata)
        self.messages.append(message)

        # 限制历史长度
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history:]

    def add_user_message(self, content: str, metadata: Optional[Dict[str, Any]] = None):
        """添加用户消息"""
        self.add_message("user", content, metadata)

    def add_assistant_message(self, content: str, metadata: Optional[Dict[str, Any]] = None):
        """添加助手消息"""
        self.add_message("assistant", content, metadata)

    def add_system_message(self, content: str, metadata: Optional[Dict[str, Any]] = None):
        """添加系统消息"""
        self.add_message("system", content, metadata)

    def get_messages(self, last_n: Optional[int] = None) -> List[Dict[str, str]]:
        """
        获取消息历史

        Args:
            last_n: 只返回最近N条消息，None表示返回全部

        Returns:
            消息字典列表
        """
        messages = self.messages[-last_n:] if last_n else self.messages
        return [{"role": msg.role, "content": msg.content} for msg in messages]

    def get_conversation_text(self, last_n: Optional[int] = None) -> str:
        """
        获取对话文本格式

        Args:
            last_n: 只返回最近N条消息

        Returns:
            格式化的对话文本
        """
        messages = self.messages[-last_n:] if last_n else self.messages
        lines = []
        for msg in messages:
            lines.append(f"{msg.role}: {msg.content}")
        return "\n".join(lines)

    def get_last_user_message(self) -> Optional[str]:
        """获取最后一条用户消息"""
        for msg in reversed(self.messages):
            if msg.role == "user":
                return msg.content
        return None

    def get_last_assistant_message(self) -> Optional[str]:
        """获取最后一条助手消息"""
        for msg in reversed(self.messages):
            if msg.role == "assistant":
                return msg.content
        return None

    def clear(self):
        """清空对话历史"""
        self.messages.clear()

    def get_summary(self) -> Dict[str, Any]:
        """
        获取对话摘要

        Returns:
            包含对话统计信息的字典
        """
        user_count = sum(1 for msg in self.messages if msg.role == "user")
        assistant_count = sum(1 for msg in self.messages if msg.role == "assistant")
        system_count = sum(1 for msg in self.messages if msg.role == "system")

        return {
            "session_id": self.session_id,
            "total_messages": len(self.messages),
            "user_messages": user_count,
            "assistant_messages": assistant_count,
            "system_messages": system_count,
            "first_message_time": self.messages[0].timestamp if self.messages else None,
            "last_message_time": self.messages[-1].timestamp if self.messages else None
        }

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典用于序列化"""
        return {
            "session_id": self.session_id,
            "max_history": self.max_history,
            "messages": [msg.to_dict() for msg in self.messages]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationMemory":
        """从字典恢复"""
        memory = cls(max_history=data.get("max_history", 100))
        memory.session_id = data.get("session_id", memory.session_id)
        memory.messages = [Message.from_dict(msg) for msg in data.get("messages", [])]
        return memory

    def save_to_file(self, filepath: str):
        """保存到文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load_from_file(cls, filepath: str) -> "ConversationMemory":
        """从文件加载"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)
