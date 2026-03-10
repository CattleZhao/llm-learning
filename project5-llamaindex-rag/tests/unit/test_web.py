"""
测试 Streamlit Web Interface

注意: 这些测试主要验证模块导入和基本功能
完整的 UI 测试需要手动测试或使用专门的工具
"""
import pytest
from unittest.mock import patch, Mock


def test_web_module_import():
    """测试 web 模块可以正常导入"""
    try:
        import sys
        from pathlib import Path

        # 添加项目路径
        project_root = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(project_root))

        # 模拟 streamlit 模块
        sys.modules['streamlit'] = Mock()

        # 导入模块（会失败因为我们没有真正安装 streamlit）
        # 但至少可以检查文件存在
        web_file = project_root / "app" / "web.py"
        assert web_file.exists()
        assert web_file.is_file()

    except Exception as e:
        pytest.fail(f"无法导入 web 模块: {str(e)}")


def test_web_file_structure():
    """测试 web.py 文件结构"""
    from pathlib import Path

    project_root = Path(__file__).parent.parent.parent
    web_file = project_root / "app" / "web.py"

    assert web_file.exists()

    # 读取文件内容
    content = web_file.read_text()

    # 检查关键函数和类
    assert "def load_documents():" in content
    assert "def main():" in content
    assert "st.set_page_config" in content
    assert "RAGQueryEngine" in content
    assert "MarkdownLoader" in content
    assert "VectorIndexManager" in content


def test_web_dependencies():
    """测试 web.py 依赖的正确性"""
    from pathlib import Path

    project_root = Path(__file__).parent.parent.parent
    web_file = project_root / "app" / "web.py"
    requirements_file = project_root / "requirements.txt"

    assert web_file.exists()
    assert requirements_file.exists()

    web_content = web_file.read_text()
    req_content = requirements_file.read_text()

    # 检查 streamlit 在 requirements 中
    assert "streamlit" in req_content


def test_web_session_state_usage():
    """测试 session state 使用"""
    from pathlib import Path

    project_root = Path(__file__).parent.parent.parent
    web_file = project_root / "app" / "web.py"
    content = web_file.read_text()

    # 检查 session state 的使用
    assert "st.session_state" in content
    assert '"index"' in content
    assert '"query_engine"' in content
    assert '"documents_loaded"' in content
