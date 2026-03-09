"""
CLI 应用测试
"""
import pytest
from app.cli import parse_arguments, print_banner


def test_parse_arguments_requires_task():
    """测试必须提供 --task 参数"""
    with pytest.raises(SystemExit):
        parse_arguments([])


def test_parse_arguments_accepts_task():
    """测试 --task 参数被接受"""
    args = parse_arguments(['--task', 'test task'])
    assert args.task == 'test task'


def test_parse_arguments_has_defaults():
    """测试 CLI 有合理的默认值"""
    args = parse_arguments(['--task', 'test'])
    assert args.model is None
    assert args.temperature is None
    assert args.debug is False
    assert args.sequential is False


def test_parse_arguments_model_option():
    """测试 --model 参数"""
    args = parse_arguments(['--task', 'test', '--model', 'gpt-4'])
    assert args.model == 'gpt-4'


def test_parse_arguments_temperature_option():
    """测试 --temperature 参数"""
    args = parse_arguments(['--task', 'test', '--temperature', '0.5'])
    assert args.temperature == 0.5


def test_parse_arguments_debug_option():
    """测试 --debug 参数"""
    args = parse_arguments(['--task', 'test', '--debug'])
    assert args.debug is True


def test_parse_arguments_sequential_option():
    """测试 --sequential 参数"""
    args = parse_arguments(['--task', 'test', '--sequential'])
    assert args.sequential is True


def test_print_banner_outputs_text(capsys):
    """测试 print_banner 有输出"""
    print_banner()
    captured = capsys.readouterr()
    assert "Multi-Agent" in captured.out
    assert "AutoGen" in captured.out
