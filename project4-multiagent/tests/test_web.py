"""
Web 应用测试
"""
import pytest


def test_web_module_imports():
    """测试 web 模块可以导入"""
    import app.web
    assert app.web is not None


def test_web_functions_exist():
    """测试关键函数存在"""
    from app.web import (
        setup_session_state,
        render_header,
        render_config_warning,
        render_sidebar,
        render_task_input,
        render_conversation_history,
        render_execution_status,
        execute_task,
        main,
    )

    # 验证这些是可调用的函数
    assert callable(setup_session_state)
    assert callable(render_header)
    assert callable(render_config_warning)
    assert callable(render_sidebar)
    assert callable(render_task_input)
    assert callable(render_conversation_history)
    assert callable(render_execution_status)
    assert callable(execute_task)
    assert callable(main)


def test_setup_session_state():
    """测试 setup_session_state 函数"""
    from streamlit import runtime
    from app.web import setup_session_state

    # 这个测试主要验证函数可以调用
    # 实际的 session state 测试需要 Streamlit 运行时
    assert callable(setup_session_state)
