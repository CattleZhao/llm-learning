"""
Orchestrator 模块

Orchestrator 负责协调所有 Agent 进行协作，实现完整的代码开发工作流。
"""
from typing import List, Optional, Dict, Any
from autogen import Agent, ConversableAgent
from src.core.config import Config
from src.agents import (
    create_user_proxy,
    create_coder,
    create_reviewer,
    create_tester,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


class CodeDevelopmentOrchestrator:
    """
    代码开发编排器

    负责管理和协调多 Agent 团队完成代码开发任务。
    """

    def __init__(
        self,
        config: Config,
        user_proxy: Optional[ConversableAgent] = None,
        coder: Optional[Agent] = None,
        reviewer: Optional[Agent] = None,
        tester: Optional[Agent] = None,
    ):
        """
        初始化编排器

        Args:
            config: 配置对象
            user_proxy: UserProxy Agent（如果不提供则自动创建）
            coder: Coder Agent（如果不提供则自动创建）
            reviewer: Reviewer Agent（如果不提供则自动创建）
            tester: Tester Agent（如果不提供则自动创建）
        """
        self.config = config

        # 创建或使用提供的 Agent
        self.user_proxy = user_proxy or create_user_proxy(config)
        self.coder = coder or create_coder(config)
        self.reviewer = reviewer or create_reviewer(config)
        self.tester = tester or create_tester(config)

        logger.info("CodeDevelopmentOrchestrator initialized with all agents")

    @property
    def agents(self) -> List[Agent]:
        """获取所有 Agent 列表"""
        return [
            self.user_proxy,
            self.coder,
            self.reviewer,
            self.tester,
        ]

    def execute_task(
        self,
        task_description: str,
        coder_first: bool = True,
    ) -> Dict[str, Any]:
        """
        执行代码开发任务

        这是核心方法，启动 Agent 团队协作完成任务。

        工作流程：
        1. UserProxy 接收任务
        2. 如果 coder_first=True，直接让 Coder 开始
        3. Agent 之间通过对话协作
        4. 返回执行结果

        Args:
            task_description: 任务描述
            coder_first: 是否从 Coder 开始（True）还是让 UserProxy 决定（False）

        Returns:
            包含执行结果的字典
        """
        logger.info(f"Executing task: {task_description[:50]}...")

        results = {
            'task': task_description,
            'conversation_history': [],
            'success': False,
        }

        try:
            if coder_first:
                # 直接从 UserProxy -> Coder 开始
                logger.info("Starting conversation: user_proxy -> coder")
                self.user_proxy.initiate_chat(
                    self.coder,
                    message=task_description,
                    clear_history=True,
                )
            else:
                # 让 UserProxy 决定如何处理任务
                logger.info("Starting conversation: user_proxy -> (auto)")
                self.user_proxy.initiate_chat(
                    message=task_description,
                    clear_history=True,
                )

            # 获取对话历史
            results['conversation_history'] = self._get_conversation_history()
            results['success'] = True

        except Exception as e:
            logger.error(f"Task execution failed: {e}", exc_info=True)
            results['error'] = str(e)

        logger.info("Task execution completed")
        return results

    def _get_conversation_history(self) -> List[Dict[str, Any]]:
        """
        提取对话历史

        Returns:
            对话消息列表
        """
        history = []

        # 从 user_proxy 获取对话历史（它存储所有对话）
        for agent in self.agents:
            if hasattr(agent, 'chat_messages'):
                for other_agent, messages in agent.chat_messages.items():
                    for msg in messages:
                        history.append({
                            'from': msg.get('role', 'unknown'),
                            'to': other_agent.name if hasattr(other_agent, 'name') else 'unknown',
                            'content': msg.get('content', ''),
                        })

        return history

    def execute_sequential_workflow(
        self,
        task_description: str,
    ) -> Dict[str, Any]:
        """
        执行顺序工作流（更可控的执行方式）

        工作流程：
        1. UserProxy -> Coder（编写代码）
        2. UserProxy -> Reviewer（审查代码）
        3. UserProxy -> Tester（编写测试）
        4. UserProxy（执行测试）

        Args:
            task_description: 任务描述

        Returns:
            包含执行结果的字典
        """
        logger.info(f"Executing sequential workflow: {task_description[:50]}...")

        results = {
            'task': task_description,
            'stages': {},
            'conversation_history': [],
            'success': False,
        }

        try:
            # 阶段 1: 请求 Coder 编写代码
            logger.info("Stage 1: Requesting code from Coder")
            coding_prompt = f"Please write code for: {task_description}"
            self.user_proxy.initiate_chat(
                self.coder,
                message=coding_prompt,
                clear_history=True,
            )

            # 阶段 2: 请求 Reviewer 审查代码
            logger.info("Stage 2: Requesting review from Reviewer")
            review_prompt = "Please review the code above"
            self.user_proxy.initiate_chat(
                self.reviewer,
                message=review_prompt,
                clear_history=False,
            )

            # 阶段 3: 请求 Tester 编写测试
            logger.info("Stage 3: Requesting tests from Tester")
            test_prompt = f"Please write tests for: {task_description}"
            self.user_proxy.initiate_chat(
                self.tester,
                message=test_prompt,
                clear_history=False,
            )

            results['success'] = True
            results['conversation_history'] = self._get_conversation_history()

        except Exception as e:
            logger.error(f"Sequential workflow failed: {e}", exc_info=True)
            results['error'] = str(e)

        return results

    def get_agent_by_name(self, name: str) -> Optional[Agent]:
        """
        通过名称获取 Agent

        Args:
            name: Agent 名称

        Returns:
            Agent 实例，如果未找到则返回 None
        """
        for agent in self.agents:
            if hasattr(agent, 'name') and agent.name == name:
                return agent
        return None


def create_orchestrator(
    config: Config,
    user_proxy: Optional[ConversableAgent] = None,
    coder: Optional[Agent] = None,
    reviewer: Optional[Agent] = None,
    tester: Optional[Agent] = None,
) -> CodeDevelopmentOrchestrator:
    """
    创建代码开发编排器（工厂函数）

    Args:
        config: 配置对象
        user_proxy: 可选的预配置 UserProxy Agent
        coder: 可选的预配置 Coder Agent
        reviewer: 可选的预配置 Reviewer Agent
        tester: 可选的预配置 Tester Agent

    Returns:
        配置好的 CodeDevelopmentOrchestrator 实例
    """
    logger.info("Creating CodeDevelopmentOrchestrator")

    orchestrator = CodeDevelopmentOrchestrator(
        config=config,
        user_proxy=user_proxy,
        coder=coder,
        reviewer=reviewer,
        tester=tester,
    )

    return orchestrator
