# src/main.py
"""
代码助手CLI - 交互式命令行界面
"""
import os
import sys
from pathlib import Path
from typing import Optional

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent))

from agents.code_assistant_agent import CodeAssistantAgent
from memory.conversation_memory import ConversationMemory
from memory.project_memory import ProjectMemory


class CodeAssistantCLI:
    """代码助手命令行界面"""

    def __init__(self, workspace_dir: str = None):
        """
        初始化CLI

        Args:
            workspace_dir: 工作目录
        """
        self.agent = CodeAssistantAgent(workspace_dir)
        self.running = True
        self.workspace_dir = workspace_dir or str(Path.cwd() / "workspace")

        print("=" * 60)
        print("        代码助手 Agent - CLI")
        print("=" * 60)
        print()
        self.show_help()

    def show_help(self):
        """显示帮助信息"""
        help_text = """
可用命令：
  /chat <message>      - 与助手对话
  /analyze <file>      - 分析代码文件
  /test <file> [func]  - 生成测试代码
  /refactor <file>     - 获取重构建议
  /history [n]         - 查看对话历史（最近n条）
  /context             - 查看当前上下文
  /search <keyword>    - 搜索项目记忆
  /stats               - 查看项目统计
  /clear               - 清空对话历史
  /exit                - 退出程序

提示：输入 /help 可随时查看此帮助信息
        """
        print(help_text)

    def run(self):
        """运行CLI主循环"""
        while self.running:
            try:
                user_input = input("\n>>> ").strip()

                if not user_input:
                    continue

                self.handle_command(user_input)

            except KeyboardInterrupt:
                print("\n\n使用 /exit 退出程序")
            except EOFError:
                print("\n\n再见！")
                break

    def handle_command(self, user_input: str):
        """
        处理用户命令

        Args:
            user_input: 用户输入
        """
        if user_input.startswith("/"):
            parts = user_input.split(maxsplit=1)
            command = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""

            if command == "/chat":
                self.cmd_chat(args)
            elif command == "/analyze":
                self.cmd_analyze(args)
            elif command == "/test":
                self.cmd_test(args)
            elif command == "/refactor":
                self.cmd_refactor(args)
            elif command == "/history":
                self.cmd_history(args)
            elif command == "/context":
                self.cmd_context()
            elif command == "/search":
                self.cmd_search(args)
            elif command == "/stats":
                self.cmd_stats()
            elif command == "/clear":
                self.cmd_clear()
            elif command == "/exit" or command == "/quit":
                self.cmd_exit()
            elif command == "/help":
                self.show_help()
            else:
                print(f"未知命令: {command}，输入 /help 查看可用命令")
        else:
            # 默认作为对话消息
            self.cmd_chat(user_input)

    def cmd_chat(self, message: str):
        """
        对话命令

        Args:
            message: 消息内容
        """
        if not message:
            print("请输入消息内容")
            return

        print("\n助手：", end="")
        response = self.agent.chat(message)
        print(response)

    def cmd_analyze(self, file_path: str):
        """
        分析命令

        Args:
            file_path: 文件路径
        """
        if not file_path:
            print("请指定要分析的文件路径")
            return

        # 支持相对路径
        if not os.path.isabs(file_path):
            file_path = os.path.join(self.workspace_dir, file_path)

        print(f"\n正在分析文件: {file_path}")

        result = self.agent.analyze_code(file_path=file_path)

        # 处理嵌套的结果结构
        if "result" in result:
            actual_result = result["result"]
            if isinstance(actual_result, dict):
                # 提取各个分析结果
                functions = actual_result.get("functions", {})
                classes = actual_result.get("classes", {})
                lines = actual_result.get("lines", {})
                imports = actual_result.get("imports", {})
                complexity = actual_result.get("complexity", {})

                # 如果结果还包含嵌套的"result"键，继续提取
                if isinstance(functions, dict) and "result" in functions:
                    functions = functions["result"]
                if isinstance(classes, dict) and "result" in classes:
                    classes = classes["result"]
                if isinstance(lines, dict) and "result" in lines:
                    lines = lines["result"]
                if isinstance(imports, dict) and "result" in imports:
                    imports = imports["result"]
                if isinstance(complexity, dict) and "result" in complexity:
                    complexity = complexity["result"]

                print("\n【分析结果】")

                if functions:
                    print(f"\n函数 ({len(functions)}个):")
                    for f in functions:
                        print(f"  - {f.get('name', 'N/A')}(): "
                              f"参数={f.get('args_count', 0)}, "
                              f"行号={f.get('line_number', 'N/A')}, "
                              f"方法={'是' if f.get('is_method') else '否'}")

                if classes:
                    print(f"\n类 ({len(classes)}个):")
                    for c in classes:
                        print(f"  - {c.get('name', 'N/A')}: "
                              f"方法={c.get('methods_count', 0)}, "
                              f"行号={c.get('line_number', 'N/A')}, "
                              f"基类={c.get('base_classes', [])}")

                if lines:
                    print(f"\n代码行数:")
                    print(f"  总行数: {lines.get('total', 0)}")
                    print(f"  代码行: {lines.get('code', 0)}")
                    print(f"  注释行: {lines.get('comments', 0)}")

                if complexity:
                    print(f"\n复杂度:")
                    print(f"  圈复杂度: {complexity.get('cyclomatic_complexity', 'N/A')}")
                    print(f"  等级: {complexity.get('level', 'N/A')}")

                if imports:
                    print(f"\n导入语句:")
                    if imports.get('standard_imports'):
                        print("  标准导入:")
                        for imp in imports['standard_imports']:
                            alias = f" as {imp['alias']}" if imp['alias'] else ""
                            print(f"    - import {imp['module']}{alias}")

                    if imports.get('from_imports'):
                        print("  From导入:")
                        for imp in imports['from_imports']:
                            names = ", ".join([f"{n['name']}" for n in imp.get('imports', [])])
                            print(f"    - from {imp['module']} import {names}")
            else:
                print(f"\n{actual_result}")
        else:
            print(f"\n{result}")

    def cmd_test(self, args: str):
        """
        生成测试命令

        Args:
            args: 文件路径 [函数名]
        """
        parts = args.split()
        if not parts:
            print("请指定文件路径")
            return

        file_path = parts[0]
        function_name = parts[1] if len(parts) > 1 else None

        # 支持相对路径
        if not os.path.isabs(file_path):
            file_path = os.path.join(self.workspace_dir, file_path)

        print(f"\n正在生成测试代码...")

        test_code = self.agent.generate_test(file_path, function_name)
        print(test_code)

    def cmd_refactor(self, file_path: str):
        """
        重构建议命令

        Args:
            file_path: 文件路径
        """
        if not file_path:
            print("请指定文件路径")
            return

        # 支持相对路径
        if not os.path.isabs(file_path):
            file_path = os.path.join(self.workspace_dir, file_path)

        print(f"\n正在分析重构建议...")

        suggestions = self.agent.suggest_refactor(file_path)
        print(suggestions)

    def cmd_history(self, args: str):
        """
        历史命令

        Args:
            args: 可选的条数限制
        """
        try:
            limit = int(args) if args else None
        except ValueError:
            print("条数必须是数字")
            return

        summary = self.agent.conversation_memory.get_summary()
        print(f"\n【对话摘要】")
        print(f"会话ID: {summary['session_id']}")
        print(f"总消息数: {summary['total_messages']}")
        print(f"用户消息: {summary['user_messages']}")
        print(f"助手消息: {summary['assistant_messages']}")
        print(f"首次消息: {summary.get('first_message_time', 'N/A')}")
        print(f"最后消息: {summary.get('last_message_time', 'N/A')}")

        messages = self.agent.conversation_memory.get_messages(last_n=limit)
        if messages:
            print(f"\n【最近{len(messages)}条消息】")
            for msg in messages:
                print(f"\n{msg['role']}: {msg['content'][:100]}{'...' if len(msg['content']) > 100 else ''}")

    def cmd_context(self):
        """显示当前上下文"""
        context = self.agent.get_context()

        print("\n【当前上下文】")

        print("\n对话摘要:")
        for k, v in context['conversation_summary'].items():
            print(f"  {k}: {v}")

        print("\n项目统计:")
        for k, v in context['project_stats'].items():
            print(f"  {k}: {v}")

        print(f"\n当前文件: {context.get('current_file', 'N/A')}")

        if context.get('recent_analyses'):
            print("\n最近分析:")
            for analysis in context['recent_analyses']:
                print(f"  - {analysis.get('type')}: {analysis.get('file')} ({analysis.get('timestamp', 'N/A')})")

    def cmd_search(self, keyword: str):
        """
        搜索命令

        Args:
            keyword: 搜索关键词
        """
        if not keyword:
            print("请输入搜索关键词")
            return

        print(f"\n正在搜索 '{keyword}'...")

        results = self.agent.search_history(keyword)

        print("\n【搜索结果】")

        if results['file_summaries']:
            print(f"\n文件摘要 ({len(results['file_summaries'])}条):")
            for item in results['file_summaries']:
                print(f"  - {item['path']}")

        if results['analysis_history']:
            print(f"\n分析历史 ({len(results['analysis_history'])}条):")
            for item in results['analysis_history']:
                print(f"  - {item.get('type')}: {item.get('file')} ({item.get('timestamp', 'N/A')})")

        if results['learnings']:
            print(f"\n学习笔记 ({len(results['learnings'])}条):")
            for item in results['learnings']:
                print(f"  - {item['topic']}: {item['content'][:50]}...")

        if not any(results.values()):
            print("未找到相关结果")

    def cmd_stats(self):
        """显示项目统计"""
        stats = self.agent.project_memory.get_stats()

        print("\n【项目统计】")
        print(f"已分析文件数: {stats['total_files_analyzed']}")
        print(f"总分析次数: {stats['total_analyses']}")
        print(f"学习笔记数: {stats['total_learnings']}")
        print(f"最后更新: {stats.get('last_updated', 'N/A')}")
        print(f"记忆文件: {stats['memory_file']}")

    def cmd_clear(self):
        """清空对话历史"""
        self.agent.clear_conversation()
        print("对话历史已清空")

    def cmd_exit(self):
        """退出程序"""
        print("\n再见！")
        self.running = False


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="代码助手Agent CLI")
    parser.add_argument("--workspace", "-w", help="工作目录路径", default=None)

    args = parser.parse_args()

    cli = CodeAssistantCLI(workspace_dir=args.workspace)
    cli.run()


if __name__ == "__main__":
    main()
