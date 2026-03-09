#!/usr/bin/env python3
"""
Multi-Agent Code Development Team - Command Line Interface
"""
import argparse
import sys
from pathlib import Path

# 添加父目录到路径以支持导入
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import get_config, create_orchestrator
from src.utils import setup_logging, get_logger

# 设置日志
setup_logging()
logger = get_logger(__name__)


def print_banner():
    """打印应用横幅"""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║   🤖 Multi-Agent Code Development Team                    ║
║   Powered by AutoGen                                       ║
╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='Multi-Agent Code Development Team',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 简单代码生成
  python -m app.cli --task "实现一个快速排序算法"

  # 使用自定义模型
  python -m app.cli --task "创建一个 FastAPI REST API" --model gpt-4

  # 调试模式
  python -m app.cli --task "写一个二分查找函数" --debug
        """
    )

    parser.add_argument(
        '--task',
        type=str,
        required=True,
        help='代码开发任务描述',
    )

    parser.add_argument(
        '--model',
        type=str,
        default=None,
        help='使用的 LLM 模型（默认：来自配置或 gpt-4o）',
    )

    parser.add_argument(
        '--temperature',
        type=float,
        default=None,
        help='LLM 温度参数（默认：来自配置或 0.7）',
    )

    parser.add_argument(
        '--max-tokens',
        type=int,
        default=None,
        help='LLM 最大 token 数（默认：来自配置或 2000）',
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='启用调试模式，输出详细日志',
    )

    parser.add_argument(
        '--sequential',
        action='store_true',
        help='使用顺序工作流（更可控的执行方式）',
    )

    return parser.parse_args()


def print_results(results: dict) -> None:
    """打印执行结果

    Args:
        results: 来自编排器的结果字典
    """
    print("\n" + "=" * 60)
    print("📊 执行结果")
    print("=" * 60)

    print(f"\n📝 任务: {results['task']}")

    if results.get('success'):
        print("✅ 状态: 成功")
    else:
        print("❌ 状态: 失败")
        if results.get('error'):
            print(f"❗ 错误: {results['error']}")

    if results.get('conversation_history'):
        history = results['conversation_history']
        print(f"\n💬 对话轮数: {len(history)}")

        # 显示最近的对话
        if history:
            print("\n" + "-" * 60)
            print("最近对话:")
            print("-" * 60)
            for msg in history[-5:]:  # 显示最后 5 条消息
                from_agent = msg.get('from', 'unknown')
                content = msg.get('content', '')
                if content:
                    # 限制内容长度
                    display_content = content[:200] + "..." if len(content) > 200 else content
                    print(f"\n[{from_agent}]:")
                    print(display_content)

    print("\n" + "=" * 60)
    print("执行完成！")
    print("=" * 60 + "\n")


def main():
    """CLI 主入口"""
    # 解析参数
    args = parse_arguments()

    # 设置日志级别
    if args.debug:
        setup_logging('DEBUG')
        logger.setLevel('DEBUG')

    # 打印横幅
    print_banner()

    try:
        # 获取或创建配置
        try:
            config = get_config()
        except ValueError as e:
            logger.error(f"配置错误: {e}")
            logger.error("请确保在 .env 文件中设置了 OPENAI_API_KEY")
            sys.exit(1)

        # 用命令行参数覆盖配置
        if args.model:
            config.model = args.model
            logger.info(f"使用模型: {config.model}")
        if args.temperature is not None:
            config.temperature = args.temperature
        if args.max_tokens is not None:
            config.max_tokens = args.max_tokens

        logger.info(f"模型配置: {config.model}, 温度: {config.temperature}")

        # 创建编排器
        logger.info("正在初始化 Agent 团队...")
        orchestrator = create_orchestrator(config)

        # 执行任务
        logger.info(f"执行任务: {args.task[:100]}...")
        print(f"\n🚀 开始任务: {args.task}\n")
        print("-" * 60 + "\n")

        if args.sequential:
            results = orchestrator.execute_sequential_workflow(args.task)
        else:
            results = orchestrator.execute_task(args.task, coder_first=True)

        # 打印结果
        print_results(results)

        logger.info("任务成功完成")

    except KeyboardInterrupt:
        logger.info("用户中断任务")
        print("\n\n⚠️  任务被用户中断")
        sys.exit(0)
    except Exception as e:
        logger.error(f"任务失败: {e}", exc_info=args.debug)
        print(f"\n\n❌ 任务失败: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
