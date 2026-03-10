"""
测试 Reviewer Agent
"""
import pytest
from unittest.mock import Mock, patch


class TestReviewerAgent:
    """测试 Reviewer Agent"""

    def test_reviewer_system_message_exists(self):
        """测试系统消息存在"""
        from src.agents.reviewer import REVIEWER_SYSTEM_MESSAGE

        assert REVIEWER_SYSTEM_MESSAGE is not None
        assert len(REVIEWER_SYSTEM_MESSAGE) > 0
        assert "代码审查" in REVIEWER_SYSTEM_MESSAGE or "review" in REVIEWER_SYSTEM_MESSAGE.lower()

    @patch('src.core.llm_setup.create_llm')
    def test_create_reviewer_agent_with_crewai(self, mock_create_llm):
        """测试创建 Reviewer agent（需要 crewai）"""
        try:
            from src.agents.reviewer import create_reviewer_agent, CREWAI_AVAILABLE, REVIEWER_SYSTEM_MESSAGE

            if not CREWAI_AVAILABLE:
                pytest.skip("CrewAI not installed - skipping agent creation test")

            # Mock LLM
            mock_llm = Mock()
            mock_create_llm.return_value = mock_llm

            # Create agent
            agent = create_reviewer_agent()

            # Verify agent properties
            assert agent is not None
            assert agent.role == '代码审查专家'
            assert '审查' in agent.goal or 'review' in agent.goal.lower()
            assert agent.backstory == REVIEWER_SYSTEM_MESSAGE
            assert agent.verbose is True
            assert agent.allow_delegation is False
            assert agent.llm == mock_llm

            # Reviewer should not need tools by default
            assert len(agent.tools) == 0

        except ImportError as e:
            pytest.skip(f"CrewAI not available: {e}")

    def test_create_reviewer_agent_without_crewai_raises_error(self):
        """测试没有 crewai 时抛出错误"""
        # Mock CREWAI_AVAILABLE to False
        with patch('src.agents.reviewer.CREWAI_AVAILABLE', False):
            from src.agents.reviewer import create_reviewer_agent

            with pytest.raises(ImportError, match="CrewAI is not installed"):
                create_reviewer_agent()

    def test_reviewer_checks_code_quality(self):
        """测试 Reviewer 关注代码质量"""
        from src.agents.reviewer import REVIEWER_SYSTEM_MESSAGE

        # Check that the system message mentions key quality aspects
        quality_keywords = ['PEP', '测试', 'test', '质量', 'quality', '性能', 'performance']
        message_lower = REVIEWER_SYSTEM_MESSAGE.lower()

        # At least some quality keywords should be present
        found_keywords = [kw for kw in quality_keywords if kw.lower() in message_lower]
        assert len(found_keywords) >= 3, f"Expected at least 3 quality keywords, found: {found_keywords}"
