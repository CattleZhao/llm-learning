"""
Code Development Crew

组合所有 Agent 和 Task，形成完整的代码开发工作流。

注意：此模块需要安装 crewai。请运行：
    pip install crewai>=1.10.0
"""

from crewai import Crew, Process

from src.agents.coordinator import create_coordinator_agent
from src.agents.coder import create_coder_agent
from src.agents.reviewer import create_reviewer_agent
from src.agents.tester import create_tester_agent
from src.tasks.coding_task import create_coding_task
from src.tasks.review_task import create_review_task
from src.tasks.testing_task import create_testing_task
from src.tasks.final_task import create_final_task


# Try to import crewai, provide helpful error if not available
try:
    from crewai import Crew, Process
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    Crew = None
    Process = None


class CodeDevelopmentCrew:
    """
    代码开发团队

    组合 Coordinator、Coder、Reviewer 和 Tester 四个 Agent，
    按照顺序执行任务：
    1. Coding - Coder 编写代码
    2. Review - Reviewer 审查代码
    3. Testing - Tester 编写和执行测试
    4. Final - Coordinator 汇总所有工作成果
    """

    def __init__(self):
        """
        初始化 Code Development Crew

        创建所有 Agent 和 Task，并配置 Crew 实例。
        """
        if not CREWAI_AVAILABLE:
            raise ImportError(
                "CrewAI is not installed. Please install it with:\n"
                "  pip install 'crewai>=1.10.0'"
            )

        # Create all agents
        self.coordinator = create_coordinator_agent()
        self.coder = create_coder_agent()
        self.reviewer = create_reviewer_agent()
        self.tester = create_tester_agent()

        # Create all tasks with proper context dependencies
        # Note: Tasks will be dynamically configured in kickoff()
        self.coding_task = None
        self.review_task = None
        self.testing_task = None
        self.final_task = None
        self.crew = None

    def _setup_tasks(self, task_description: str):
        """
        设置所有任务，建立正确的依赖关系

        Args:
            task_description: 用户提供的任务描述
        """
        # Create tasks with proper context chain
        self.coding_task = create_coding_task(
            self.coder,
            description=f"任务: {task_description}\n\n请根据上述任务需求编写 Python 代码。"
        )

        self.review_task = create_review_task(
            self.reviewer,
            context=[self.coding_task]
        )

        self.testing_task = create_testing_task(
            self.tester,
            context=[self.coding_task, self.review_task]
        )

        self.final_task = create_final_task(
            self.coordinator,
            context=[self.coding_task, self.review_task, self.testing_task]
        )

        # Create crew with sequential process
        self.crew = Crew(
            agents=[self.coordinator, self.coder, self.reviewer, self.tester],
            tasks=[self.coding_task, self.review_task, self.testing_task, self.final_task],
            process=Process.sequential,
            verbose=True
        )

    def kickoff(self, task_description: str):
        """
        启动 Crew 执行任务

        Args:
            task_description: 用户提供的任务描述

        Returns:
            Crew 执行结果
        """
        # Setup tasks with the provided description
        self._setup_tasks(task_description)

        # Execute the crew
        return self.crew.kickoff()
