"""
Integration Tests for Code Development Crew

These tests require real API keys and make actual LLM calls.
Mark with @pytest.mark.integration
"""
import pytest
import os
from src.crews.code_crew import CodeDevelopmentCrew


@pytest.mark.integration
def test_simple_algorithm_end_to_end():
    """Test simple algorithm implementation end-to-end"""
    if not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip("需要 ANTHROPIC_API_KEY")

    crew = CodeDevelopmentCrew()
    result = crew.kickoff("实现一个计算两数之和的函数")
    assert result is not None
    assert len(result) > 0


@pytest.mark.integration
def test_crew_has_all_agents():
    """Test that crew has all required agents"""
    if not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip("需要 ANTHROPIC_API_KEY")

    crew = CodeDevelopmentCrew()
    assert crew.coordinator is not None
    assert crew.coder is not None
    assert crew.reviewer is not None
    assert crew.tester is not None


@pytest.mark.integration
def test_crew_can_be_instantiated():
    """Test that crew can be instantiated without errors"""
    if not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip("需要 ANTHROPIC_API_KEY")

    crew = CodeDevelopmentCrew()
    assert crew is not None
    assert hasattr(crew, 'coordinator')
    assert hasattr(crew, 'coder')
    assert hasattr(crew, 'reviewer')
    assert hasattr(crew, 'tester')


@pytest.mark.integration
def test_fibonacci_algorithm():
    """Test Fibonacci algorithm implementation"""
    if not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip("需要 ANTHROPIC_API_KEY")

    crew = CodeDevelopmentCrew()
    result = crew.kickoff("实现一个计算斐波那契数列的函数")
    assert result is not None
    assert len(result) > 0


@pytest.mark.integration
def test_csv_processing_task():
    """Test CSV data processing task"""
    if not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip("需要 ANTHROPIC_API_KEY")

    crew = CodeDevelopmentCrew()
    result = crew.kickoff("创建一个处理 CSV 数据的脚本")
    assert result is not None
    assert len(result) > 0
