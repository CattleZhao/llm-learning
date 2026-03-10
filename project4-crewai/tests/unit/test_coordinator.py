"""
测试 Coordinator Agent
"""
import pytest
from unittest.mock import Mock, patch


class TestCoordinatorAgent:
    """测试 Coordinator Agent"""

    def test_coordinator_system_message_exists(self):
        """测试系统消息存在"""
        from src.agents.coordinator import COORDINATOR_SYSTEM_MESSAGE

        assert COORDINATOR_SYSTEM_MESSAGE is not None
        assert len(COORDINATOR_SYSTEM_MESSAGE) > 0
        assert "协调" in COORDINATOR_SYSTEM_MESSAGE or "coordinator" in COORDINATOR_SYSTEM_MESSAGE.lower()

    @patch('src.core.llm_setup.create_llm')
    def test_create_coordinator_agent_with_crewai(self, mock_create_llm):
        """测试创建 Coordinator agent（需要 crewai）"""
        try:
            from src.agents.coordinator import create_coordinator_agent, CREWAI_AVAILABLE, COORDINATOR_SYSTEM_MESSAGE

            if not CREWAI_AVAILABLE:
                pytest.skip("CrewAI not installed - skipping agent creation test")

            # Mock LLM
            mock_llm = Mock()
            mock_create_llm.return_value = mock_llm

            # Create agent
            agent = create_coordinator_agent()

            # Verify agent properties
            assert agent is not None
            assert agent.role == '项目协调员'
            assert '协调' in agent.goal or 'coordinate' in agent.goal.lower()
            assert agent.backstory == COORDINATOR_SYSTEM_MESSAGE
            assert agent.verbose is True
            # Coordinator should allow delegation to manage other agents
            assert agent.allow_delegation is True
            assert agent.llm == mock_llm

            # Coordinator typically doesn't need direct tools
            assert len(agent.tools) == 0

        except ImportError as e:
            pytest.skip(f"CrewAI not available: {e}")

    def test_create_coordinator_agent_without_crewai_raises_error(self):
        """测试没有 crewai 时抛出错误"""
        # Mock CREWAI_AVAILABLE to False
        with patch('src.agents.coordinator.CREWAI_AVAILABLE', False):
            from src.agents.coordinator import create_coordinator_agent

            with pytest.raises(ImportError, match="CrewAI is not installed"):
                create_coordinator_agent()

    def test_coordinator_can_delegate(self):
        """测试 Coordinator 可以委托任务"""
        from src.agents.coordinator import COORDINATOR_SYSTEM_MESSAGE

        # Check that the system message mentions delegation or coordination
        message_lower = COORDINATOR_SYSTEM_MESSAGE.lower()
        coordination_keywords = ['delegate', '委托', 'coordinate', '协调', 'manage', '管理', 'assign', '分配']

        found_keywords = [kw for kw in coordination_keywords if kw.lower() in message_lower]
        assert len(found_keywords) >= 2, f"Expected at least 2 coordination keywords, found: {found_keywords}"

    def test_coordinator_oversees_workflow(self):
        """测试 Coordinator 监督工作流程"""
        from src.agents.coordinator import COORDINATOR_SYSTEM_MESSAGE

        # Check that the system message mentions workflow oversight
        message_lower = COORDINATOR_SYSTEM_MESSAGE.lower()
        workflow_keywords = [
            'workflow', '工作流',
            'process', '流程',
            'coder', 'reviewer', 'tester',
            '代码', '审查', '测试'
        ]

        found_keywords = [kw for kw in workflow_keywords if kw.lower() in message_lower]
        assert len(found_keywords) >= 3, f"Expected at least 3 workflow keywords, found: {found_keywords}"
