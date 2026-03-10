import os
import pytest
from pathlib import Path
from src.tools.file_writer import write_file, FileWriterTool

def test_write_file_creates_file(tmp_path):
    """测试写入文件创建文件"""
    file_path = tmp_path / "test.py"
    content = "def hello():\n    return 'world'"

    result = write_file(str(file_path), content)

    assert result["success"] is True
    assert result["file_path"] == str(file_path)
    assert file_path.exists()
    assert file_path.read_text() == content

def test_write_file_creates_directories(tmp_path):
    """测试写入文件时自动创建目录"""
    file_path = tmp_path / "nested" / "dir" / "test.py"
    content = "# test file"

    result = write_file(str(file_path), content)

    assert result["success"] is True
    assert file_path.exists()
    assert file_path.parent.exists()

def test_write_file_to_outputs_dir(tmp_path, monkeypatch):
    """测试写入到 outputs 目录"""
    from src.core.config import Config, set_config
    monkeypatch.setenv("CODE_EXECUTION_WORK_DIR", str(tmp_path))
    # Reset config to pick up new work directory
    set_config(Config(api_key="test-key-for-testing", work_dir=str(tmp_path)))

    result = write_file("solution.py", "def solution():\n    pass")

    assert result["success"] is True
    expected_path = tmp_path / "solution.py"
    assert expected_path.exists()

def test_write_file_overwrites_existing(tmp_path):
    """测试覆盖已存在的文件"""
    file_path = tmp_path / "test.py"
    file_path.write_text("old content")

    write_file(str(file_path), "new content")

    assert file_path.read_text() == "new content"

def test_FileWriterTool_schema():
    """测试 FileWriterTool 的 schema"""
    tool = FileWriterTool()
    schema = tool.get_schema()

    assert "file_path" in schema["properties"]
    assert "content" in schema["properties"]
