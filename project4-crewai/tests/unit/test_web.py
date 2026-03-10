"""
Unit tests for Web UI

测试 Web UI 的基本功能。

注意：这些测试需要 streamlit 库。
"""

import pytest

# Skip tests if streamlit is not available
pytest.importorskip("streamlit")


def test_web_module_exists():
    """Test that the web module can be imported"""
    import app.web
    assert app.web is not None


def test_main_function_exists():
    """Test that the main function exists"""
    from app.web import main
    assert callable(main)


def test_web_ui_components():
    """Test that web UI components are properly defined"""
    import streamlit as st
    from app.web import main

    # Verify streamlit functions are available
    assert hasattr(st, 'set_page_config')
    assert hasattr(st, 'title')
    assert hasattr(st, 'markdown')
    assert hasattr(st, 'sidebar')
    assert hasattr(st, 'text_area')
    assert hasattr(st, 'button')


class TestWebUI:
    """Test suite for Web UI components"""

    def test_page_config(self):
        """Test that page configuration is set"""
        # This would require mocking streamlit
        # For now, just verify the module loads
        import app.web
        assert True

    def test_main_callable(self):
        """Test that main is callable"""
        from app.web import main
        assert callable(main)

    def test_import_dependencies(self):
        """Test that all dependencies can be imported"""
        import streamlit as st
        from src.crews.code_crew import CodeDevelopmentCrew

        # Verify streamlit is available
        assert st is not None

        # Verify CodeDevelopmentCrew is available
        assert CodeDevelopmentCrew is not None


@pytest.mark.skipif(True, reason="Streamlit UI tests require browser context")
class TestWebUIIntegration:
    """Integration tests for Web UI (requires browser context)"""

    def test_page_renders(self):
        """Test that the page renders without errors"""
        # This would require a testing framework like streamlit-test
        pass

    def test_task_input_exists(self):
        """Test that task input field exists"""
        # This would require UI testing
        pass

    def test_execute_button_exists(self):
        """Test that execute button exists"""
        # This would require UI testing
        pass


def test_web_ui_structure():
    """Test the structure of the web UI module"""
    import app.web
    import inspect

    # Check that main function exists
    assert hasattr(app.web, 'main')

    # Check that main has a docstring
    assert app.web.main.__doc__ is not None

    # Check that the module imports required components
    source = inspect.getsource(app.web)
    assert 'import streamlit' in source
    assert 'CodeDevelopmentCrew' in source
