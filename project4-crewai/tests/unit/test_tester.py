"""
测试 Tester Agent
"""
import pytest
from unittest.mock import Mock, patch


class TestTesterAgent:
    """测试 Tester Agent"""

    def test_tester_system_message_exists(self):
        """测试系统消息存在"""
        from src.agents.tester import TESTER_SYSTEM_MESSAGE

        assert TESTER_SYSTEM_MESSAGE is not None
        assert len(TESTER_SYSTEM_MESSAGE) > 0
        assert "测试" in TESTER_SYSTEM_MESSAGE or "test" in TESTER_SYSTEM_MESSAGE.lower()

    @patch('src.core.llm_setup.create_llm')
    def test_create_tester_agent_with_crewai(self, mock_create_llm):
        """测试创建 Tester agent（需要 crewai）"""
        try:
            from src.agents.tester import create_tester_agent, CREWAI_AVAILABLE, TESTER_SYSTEM_MESSAGE

            if not CREWAI_AVAILABLE:
                pytest.skip("CrewAI not installed - skipping agent creation test")

            # Mock LLM
            mock_llm = Mock()
            mock_create_llm.return_value = mock_llm

            # Create agent
            agent = create_tester_agent()

            # Verify agent properties
            assert agent is not None
            assert agent.role == '测试工程师'
            assert '测试' in agent.goal or 'test' in agent.goal.lower()
            assert agent.backstory == TESTER_SYSTEM_MESSAGE
            assert agent.verbose is True
            assert agent.allow_delegation is False
            assert agent.llm == mock_llm

            # Verify tools
            assert len(agent.tools) == 2
            tool_names = {tool.name for tool in agent.tools}
            assert "write_file" in tool_names
            assert "execute_code" in tool_names

        except ImportError as e:
            pytest.skip(f"CrewAI not available: {e}")

    @patch('src.core.llm_setup.create_llm')
    def test_tester_has_required_tools(self, mock_create_llm):
        """测试 Tester agent 有所需的工具"""
        try:
            from src.agents.tester import create_tester_agent, CREWAI_AVAILABLE

            if not CREWAI_AVAILABLE:
                pytest.skip("CrewAI not installed")

            mock_llm = Mock()
            mock_create_llm.return_value = mock_llm

            agent = create_tester_agent()

            # Check that tools are correct types
            from src.tools.file_writer import FileWriterTool
            from src.tools.code_executor import CodeExecutorTool

            tool_classes = {type(tool) for tool in agent.tools}
            assert FileWriterTool in tool_classes
            assert CodeExecutorTool in tool_classes

        except ImportError:
            pytest.skip("CrewAI not installed")

    def test_create_tester_agent_without_crewai_raises_error(self):
        """测试没有 crewai 时抛出错误"""
        # Mock CREWAI_AVAILABLE to False
        with patch('src.agents.tester.CREWAI_AVAILABLE', False):
            from src.agents.tester import create_tester_agent

            with pytest.raises(ImportError, match="CrewAI is not installed"):
                create_tester_agent()

    def test_tester_focuses_on_test_quality(self):
        """测试 Tester 关注测试质量"""
        from src.agents.tester import TESTER_SYSTEM_MESSAGE

        # Check that the system message mentions key testing aspects
        quality_keywords = [
            'pytest', '单元测试', 'unit test',
            '覆盖率', 'coverage',
            '边界', 'edge case',
            '断言', 'assert'
        ]
        message_lower = TESTER_SYSTEM_MESSAGE.lower()

        # At least some testing keywords should be present
        found_keywords = [kw for kw in quality_keywords if kw.lower() in message_lower]
        assert len(found_keywords) >= 3, f"Expected at least 3 testing keywords, found: {found_keywords}"
