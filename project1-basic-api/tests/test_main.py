# tests/test_main.py
from unittest.mock import patch
import pytest

def test_main_menu_exists():
    """测试主菜单函数存在"""
    from src.main import main, print_menu
    assert callable(main)
    assert callable(print_menu)
