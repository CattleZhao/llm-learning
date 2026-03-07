# tests/test_memory.py
"""
测试记忆系统
"""
import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from memory.conversation_memory import ConversationMemory, Message
from memory.project_memory import ProjectMemory


def test_conversation_memory():
    """测试对话记忆"""
    print("测试对话记忆...")

    memory = ConversationMemory(max_history=10)

    # 添加消息
    memory.add_user_message("你好")
    memory.add_assistant_message("你好！有什么可以帮助你的？")
    memory.add_user_message("分析这个文件")

    # 获取摘要
    summary = memory.get_summary()
    print(f"  对话摘要: {summary}")

    # 获取消息
    messages = memory.get_messages()
    print(f"  消息数量: {len(messages)}")

    # 获取对话文本
    text = memory.get_conversation_text()
    print(f"  对话文本:\n{text}")

    print("  对话记忆测试通过！\n")


def test_project_memory():
    """测试项目记忆"""
    print("测试项目记忆...")

    memory = ProjectMemory()

    # 设置项目信息
    memory.set_project_info("name", "test_project")
    memory.set_project_info("language", "Python")

    # 保存文件摘要
    memory.save_file_summary("test.py", {
        "functions": 5,
        "classes": 1,
        "lines": 100
    })

    # 添加分析历史
    memory.add_analysis_history("code_analysis", "test.py", {"complexity": "low"})

    # 添加学习笔记
    memory.add_learning("AST", "Python的ast模块用于解析代码结构")

    # 获取统计
    stats = memory.get_stats()
    print(f"  项目统计: {stats}")

    # 搜索
    results = memory.search_memory("AST")
    print(f"  搜索结果: {results}")

    print("  项目记忆测试通过！\n")


if __name__ == "__main__":
    test_conversation_memory()
    test_project_memory()
    print("所有测试通过！")
