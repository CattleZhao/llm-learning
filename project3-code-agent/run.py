#!/usr/bin/env python3
"""
代码助手Agent - 启动脚本

用法：
    python run.py
    python run.py --workspace ./my-project
"""
import sys
from pathlib import Path

# 将项目根目录和src目录添加到Python路径
project_root = Path(__file__).parent
src_dir = project_root / "src"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_dir))

# 导入并运行CLI
from src.main import main

if __name__ == "__main__":
    main()
