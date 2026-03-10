"""
测试 Coder Agent
"""
import pytest
from unittest.mock import Mock, patch


class TestCoderAgent:
    """测试 Coder Agent"""

    def test_coder_system_message_exists(self):
        """测试系统消息存在"""
        from src.agents.coder import CODER_SYSTEM_MESSAGE

        assert CODER_SYSTEM_MESSAGE is not None
        assert len(CODER_SYSTEM_MESSAGE) > 0
        assert "Python" in CODER_SYSTEM_MESSAGE or "python" in CODER_SYSTEM_MESSAGE.lower()

    @patch('src.core.llm_setup.create_llm')
    def test_create_coder_agent_with_crewai(self, mock_create_llm):
        """测试创建 Coder agent（需要 crewai）"""
        try:
            from src.agents.coder import create_coder_agent, CREWAI_AVAILABLE, CODER_SYSTEM_MESSAGE

            if not CREWAI_AVAILABLE:
                pytest.skip("CrewAI not installed - skipping agent creation test")

            # Mock LLM
            mock_llm = Mock()
            mock_create_llm.return_value = mock_llm

            # Create agent
            agent = create_coder_agent()

            # Verify agent properties
            assert agent is not None
            assert agent.role == '高级软件工程师'
            assert agent.goal == '编写高质量、符合最佳实践的 Python 代码'
            assert agent.backstory == CODER_SYSTEM_MESSAGE
            assert agent.verbose is True
            assert agent.allow_delegation is False
            assert agent.llm == mock_llm

            # Verify tools
            assert len(agent.tools) == 1
            assert agent.tools[0].name == "write_file"

        except ImportError as e:
            pytest.skip(f"CrewAI not available: {e}")

    @patch('src.core.llm_setup.create_llm')
    def test_coder_has_file_writer_tool(self, mock_create_llm):
        """测试 Coder agent 有 FileWriterTool"""
        try:
            from src.agents.coder import create_coder_agent, CREWAI_AVAILABLE

            if not CREWAI_AVAILABLE:
                pytest.skip("CrewAI not installed")

            mock_llm = Mock()
            mock_create_llm.return_value = mock_llm

            agent = create_coder_agent()

            # Check that the tool is FileWriterTool
            from src.tools.file_writer import FileWriterTool
            assert isinstance(agent.tools[0], FileWriterTool)

        except ImportError:
            pytest.skip("CrewAI not installed")

    def test_create_coder_agent_without_crewai_raises_error(self):
        """测试没有 crewai 时抛出错误"""
        # Mock CREWAI_AVAILABLE to False
        with patch('src.agents.coder.CREWAI_AVAILABLE', False):
            from src.agents.coder import create_coder_agent

            with pytest.raises(ImportError, match="CrewAI is not installed"):
                create_coder_agent()
