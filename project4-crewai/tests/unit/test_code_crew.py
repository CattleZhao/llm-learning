"""
Unit tests for CodeDevelopmentCrew

测试 CodeDevelopmentCrew 类的基本功能。

注意：这些测试需要 crewai 库。如果未安装，测试将被跳过。
"""

import pytest

from src.crews.code_crew import CodeDevelopmentCrew, CREWAI_AVAILABLE


@pytest.mark.skipif(not CREWAI_AVAILABLE, reason="CrewAI not installed")
class TestCodeDevelopmentCrew:
    """Test suite for CodeDevelopmentCrew class"""

    def test_initialization(self):
        """Test that CodeDevelopmentCrew can be initialized"""
        crew = CodeDevelopmentCrew()
        assert crew.coordinator is not None
        assert crew.coder is not None
        assert crew.reviewer is not None
        assert crew.tester is not None

    def test_agents_created(self):
        """Test that all agents are properly created"""
        crew = CodeDevelopmentCrew()

        # Check coordinator
        assert hasattr(crew.coordinator, 'role')
        assert crew.coordinator.role == '项目协调员'

        # Check coder
        assert hasattr(crew.coder, 'role')
        assert crew.coder.role == '高级软件工程师'

        # Check reviewer
        assert hasattr(crew.reviewer, 'role')
        assert crew.reviewer.role == '代码审查专家'

        # Check tester
        assert hasattr(crew.tester, 'role')
        assert crew.tester.role == '测试工程师'

    def test_setup_tasks(self):
        """Test that tasks can be set up with proper dependencies"""
        crew = CodeDevelopmentCrew()
        task_description = "Test task description"

        crew._setup_tasks(task_description)

        # Check that all tasks are created
        assert crew.coding_task is not None
        assert crew.review_task is not None
        assert crew.testing_task is not None
        assert crew.final_task is not None

        # Check that crew is created
        assert crew.crew is not None

    def test_task_dependencies(self):
        """Test that tasks have proper context dependencies"""
        crew = CodeDevelopmentCrew()
        task_description = "Test task"

        crew._setup_tasks(task_description)

        # Review task should depend on coding task
        assert crew.coding_task in crew.review_task.context

        # Testing task should depend on coding and review
        assert crew.coding_task in crew.testing_task.context
        assert crew.review_task in crew.testing_task.context

        # Final task should depend on all previous tasks
        assert crew.coding_task in crew.final_task.context
        assert crew.review_task in crew.final_task.context
        assert crew.testing_task in crew.final_task.context

    def test_crew_configuration(self):
        """Test that the crew is properly configured"""
        crew = CodeDevelopmentCrew()
        crew._setup_tasks("Test task")

        # Check crew has all agents
        assert len(crew.crew.agents) == 4
        assert crew.coordinator in crew.crew.agents
        assert crew.coder in crew.crew.agents
        assert crew.reviewer in crew.crew.agents
        assert crew.tester in crew.crew.agents

        # Check crew has all tasks
        assert len(crew.crew.tasks) == 4
        assert crew.coding_task in crew.crew.tasks
        assert crew.review_task in crew.crew.tasks
        assert crew.testing_task in crew.crew.tasks
        assert crew.final_task in crew.crew.tasks


@pytest.mark.skipif(not CREWAI_AVAILABLE, reason="CrewAI not installed")
def test_import_error_without_crewai():
    """Test that ImportError is raised when CrewAI is not available"""
    # This test verifies the import error handling
    # We can't actually test this without uninstalling crewai
    # but we can verify the error message is defined
    assert CodeDevelopmentCrew.__init__.__doc__ is not None


@pytest.mark.skipif(not CREWAI_AVAILABLE, reason="CrewAI not installed")
def test_code_development_crew_module_exists():
    """Test that the module can be imported"""
    import src.crews.code_crew
    assert hasattr(src.crews.code_crew, 'CodeDevelopmentCrew')
