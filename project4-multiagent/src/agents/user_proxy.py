"""
UserProxy Agent 模块

UserProxy 是协调者 Agent，负责：
1. 接收用户需求并传达给团队
2. 协调 Coder、Reviewer、Tester 之间的协作
3. 执行生成的代码并验证结果
4. 汇总最终成果并反馈给用户
"""
from typing import Optional
from autogen import UserProxyAgent
from autogen.coding import DockerCommandLineCodeExecutor, CommandLineCodeExecutor
from src.core.config import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ========== UserProxy 的系统消息 ==========
USER_PROXY_SYSTEM_MESSAGE = """You are a user proxy agent responsible for coordinating the development team.

Your responsibilities:
1. **Understand Requirements**: Understand user requirements and communicate them clearly to the team
2. **Coordinate**: Coordinate between Coder, Reviewer, and Tester agents
3. **Execute Code**: Execute generated code and verify results
4. **Report Results**: Summarize final results and provide clear feedback to the user

Communication style:
- Be concise and clear in your messages
- Provide context when delegating tasks
- Summarize outcomes clearly
- Ask for clarification when requirements are ambiguous

When you receive code from the Coder:
- Review it briefly
- Pass it to the Reviewer for detailed review
- After review approval, ask the Tester to write tests
- Execute the tests and report results

Your goal is to ensure the team produces high-quality, working code that meets the user's requirements.

IMPORTANT:
- When the task is complete, respond with "TERMINATE"
- Keep conversations focused and efficient
- If you need clarification, ask specific questions
"""


def create_user_proxy(
    config: Config,
    name: str = "user_proxy",
    system_message: Optional[str] = None,
) -> UserProxyAgent:
    """
    创建一个 UserProxy agent

    UserProxy 是协调者，负责协调其他 agent 完成开发任务。

    Args:
        config: 配置对象
        name: Agent 名称
        system_message: 系统消息（如果不提供则使用默认）

    Returns:
        配置好的 UserProxyAgent 实例
    """
    logger.info(f"Creating UserProxy agent: {name}")

    # 使用默认值或提供自定义值
    if system_message is None:
        system_message = USER_PROXY_SYSTEM_MESSAGE

    # 创建代码执行器
    if config.use_docker:
        executor = DockerCommandLineCodeExecutor(work_dir=config.work_dir)
    else:
        executor = CommandLineCodeExecutor(work_dir=config.work_dir)

    # 创建 Agent，使用新的 API
    agent = UserProxyAgent(
        name=name,
        system_message=system_message,
        code_executor=executor,
    )

    logger.info(f"UserProxy agent '{name}' created successfully")
    return agent


def create_user_proxy_for_web(
    config: Config,
    name: str = "user_proxy",
) -> UserProxyAgent:
    """
    创建专门用于 Web 界面的 UserProxy agent

    Web 界面需要不同的配置，因为交互方式不同。

    Args:
        config: 配置对象
        name: Agent 名称

    Returns:
        配置好的 UserProxyAgent 实例
    """
    logger.info(f"Creating UserProxy agent for web: {name}")

    # 创建代码执行器
    if config.use_docker:
        executor = DockerCommandLineCodeExecutor(work_dir=config.work_dir)
    else:
        executor = CommandLineCodeExecutor(work_dir=config.work_dir)

    agent = UserProxyAgent(
        name=name,
        system_message=USER_PROXY_SYSTEM_MESSAGE,
        code_executor=executor,
    )

    logger.info(f"Web UserProxy agent '{name}' created successfully")
    return agent
