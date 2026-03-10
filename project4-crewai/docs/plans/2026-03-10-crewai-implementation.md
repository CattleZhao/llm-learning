# Project 4 CrewAI Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 使用 CrewAI 框架实现多 Agent 代码开发团队系统，支持 CLI 和 Web 两种交互方式。

**Architecture:** 使用 CrewAI 作为 Agent 编排框架，LangChain 的 ChatAnthropic 作为 LLM 提供商。系统包含 4 个 Agent（Coordinator、Coder、Reviewer、Tester）和相应的 Tasks/Tools，通过 Sequential Process 协作完成任务。

**Tech Stack:** CrewAI 0.80.0, LangChain, Anthropic Claude API, Streamlit, Typer, pytest

---

## Project Setup

### Task 1: Initialize Project Structure

**Files:**
- Create: All directories
- Create: `README.md`
- Create: `.env.example`
- Create: `requirements.txt`

**Step 1: Create directory structure**

```bash
cd /root/Learn/llm-learning/project4-crewai
mkdir -p src/{agents,crews,tasks,tools,core,utils}
mkdir -p app
mkdir -p tests/{unit,integration,fixtures}
mkdir -p outputs
mkdir -p docs/plans
touch src/__init__.py src/agents/__init__.py src/crews/__init__.py
touch src/tasks/__init__.py src/tools/__init__.py src/core/__init__.py src/utils/__init__.py
touch app/__init__.py
```

**Step 2: Create README.md**

```markdown
# Project 4: Multi-Agent Code Development Team (CrewAI Version)

> 使用 CrewAI 框架实现的多 Agent 协作系统

## 项目简介

这是 Project 4 的 CrewAI 实现版本，与 AutoGen 版本进行对比学习。

## Agent 角色

| Agent | 角色定位 | 主要职责 |
|-------|---------|---------|
| **Coordinator** | 项目经理 | 协调任务流程，分配任务 |
| **Coder** | 高级工程师 | 编写高质量 Python 代码 |
| **Reviewer** | 代码审查专家 | 检查代码质量，提出改进建议 |
| **Tester** | 测试工程师 | 编写和执行测试用例 |

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，添加 ANTHROPIC_API_KEY

# 运行 CLI
python -m app.cli --task "实现快速排序算法"

# 运行 Web UI
streamlit run app/web.py
```

## 技术栈

- **CrewAI** - 多 Agent 编排框架
- **LangChain** - LLM 集成
- **Anthropic Claude** - LLM 提供商
- **Streamlit** - Web 界面
- **Typer** - CLI 框架
```

**Step 3: Create .env.example**

```bash
# Anthropic API
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Model Configuration
ANTHROPIC_MODEL=claude-sonnet-4-20250514
TEMPERATURE=0.7
MAX_TOKENS=2000

# Code Execution
CODE_EXECUTION_WORK_DIR=./outputs

# Logging
LOG_LEVEL=INFO
```

**Step 4: Create requirements.txt**

```txt
# Core Framework
crewai==0.80.0
langchain>=0.3.0
langchain-anthropic>=0.2.0

# LLM Provider
anthropic>=0.40.0

# Web UI
streamlit>=1.28.0

# CLI
typer>=0.12.0
rich>=13.0.0

# Environment
python-dotenv>=1.0.0

# Testing
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-mock>=3.12.0

# Utilities
tenacity>=8.2.0
```

**Step 5: Initialize git and commit**

```bash
cd /root/Learn/llm-learning/project4-crewai
git init
git add .
git commit -m "feat: initialize project structure"
```

---

## Core Infrastructure

### Task 2: Implement Configuration Module

**Files:**
- Create: `src/core/config.py`
- Test: `tests/unit/test_config.py`

**Step 1: Write the failing test**

Create `tests/unit/test_config.py`:

```python
import os
import pytest
from src.core.config import Config, get_config

def test_config_loads_from_env(monkeypatch):
    """测试从环境变量加载配置"""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
    monkeypatch.setenv("TEMPERATURE", "0.5")
    monkeypatch.setenv("CODE_EXECUTION_WORK_DIR", "/tmp/test")

    config = Config()
    assert config.api_key == "test-key"
    assert config.model == "claude-3-5-sonnet-20241022"
    assert config.temperature == 0.5
    assert config.work_dir == "/tmp/test"

def test_config_default_values(monkeypatch):
    """测试默认配置值"""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    # 清除其他环境变量
    for key in ["ANTHROPIC_MODEL", "TEMPERATURE", "MAX_TOKENS", "CODE_EXECUTION_WORK_DIR"]:
        monkeypatch.delenv(key, raising=False)

    config = Config()
    assert config.model == "claude-sonnet-4-20250514"
    assert config.temperature == 0.7
    assert config.max_tokens == 2000
    assert config.work_dir == "./outputs"

def test_config_requires_api_key(monkeypatch):
    """测试缺少 API key 时抛出错误"""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY is required"):
        Config()

def test_get_config_singleton(monkeypatch):
    """测试单例模式"""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    config1 = get_config()
    config2 = get_config()
    assert config1 is config2

def test_work_dir_created(monkeypatch, tmp_path):
    """测试工作目录自动创建"""
    work_dir = str(tmp_path / "outputs")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("CODE_EXECUTION_WORK_DIR", work_dir)

    config = Config()
    assert os.path.exists(work_dir)
```

**Step 2: Run test to verify it fails**

```bash
cd /root/Learn/llm-learning/project4-crewai
pytest tests/unit/test_config.py -v
```

Expected: `ModuleNotFoundError: No module named 'src.core.config'`

**Step 3: Write minimal implementation**

Create `src/core/config.py`:

```python
"""
配置管理模块

负责管理所有项目配置，包括 API key、模型设置、代码执行配置等。
"""
import os
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


@dataclass
class Config:
    """
    项目配置类

    所有配置都可以通过环境变量设置，如果没有设置则使用默认值。
    """

    # ========== Anthropic 配置 ==========
    api_key: str = field(default_factory=lambda: os.getenv('ANTHROPIC_API_KEY', ''))
    model: str = field(default_factory=lambda: os.getenv('ANTHROPIC_MODEL', 'claude-sonnet-4-20250514'))
    temperature: float = field(default_factory=lambda: float(os.getenv('TEMPERATURE', '0.7')))
    max_tokens: int = field(default_factory=lambda: int(os.getenv('MAX_TOKENS', '2000')))

    # ========== 代码执行配置 ==========
    work_dir: str = field(default_factory=lambda: os.getenv('CODE_EXECUTION_WORK_DIR', './outputs'))

    # ========== 日志配置 ==========
    log_level: str = field(default_factory=lambda: os.getenv('LOG_LEVEL', 'INFO'))

    def __post_init__(self):
        """初始化后验证"""
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY is required. "
                "请设置环境变量或在 .env 文件中配置你的 API key。"
            )

        # 确保工作目录存在
        os.makedirs(self.work_dir, exist_ok=True)


# ========== 全局配置实例管理 ==========
_config: Optional[Config] = None


def get_config() -> Config:
    """
    获取全局配置实例（单例模式）

    Returns:
        Config 实例
    """
    global _config
    if _config is None:
        _config = Config()
    return _config


def set_config(config: Config) -> None:
    """
    设置全局配置实例（主要用于测试）

    Args:
        config: Config 实例
    """
    global _config
    _config = config
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/unit/test_config.py -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/core/config.py tests/unit/test_config.py
git commit -m "feat: add configuration module with environment variable support"
```

---

### Task 3: Implement Logger Module

**Files:**
- Create: `src/utils/logger.py`

**Step 1: Create logger implementation**

Create `src/utils/logger.py`:

```python
"""
日志工具模块

提供统一的日志接口，支持彩色输出（使用 Rich）。
"""
import logging
import sys
from typing import Optional

# 全局 logger 缓存
_loggers: dict = {}


def setup_logging(level: str = 'INFO') -> None:
    """
    设置全局日志配置

    Args:
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR)
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    # 配置根 logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[logging.StreamHandler(sys.stdout)]
    )


def get_logger(name: str) -> logging.Logger:
    """
    获取或创建 Logger 实例

    Args:
        name: Logger 名称

    Returns:
        Logger 实例
    """
    if name not in _loggers:
        _loggers[name] = logging.getLogger(name)
    return _loggers[name]
```

**Step 2: Commit**

```bash
git add src/utils/logger.py
git commit -m "feat: add logger utility module"
```

---

### Task 4: Implement LLM Setup Module

**Files:**
- Create: `src/core/llm_setup.py`
- Test: `tests/unit/test_llm_setup.py`

**Step 1: Write the failing test**

Create `tests/unit/test_llm_setup.py`:

```python
import pytest
from unittest.mock import Mock, patch
from src.core.llm_setup import create_llm, create_crewai_llm

def test_create_llm_returns_chat_anthropic(monkeypatch):
    """测试 create_llm 返回 ChatAnthropic 实例"""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    with patch('src.core.llm_setup.ChatAnthropic') as mock_chat:
        mock_instance = Mock()
        mock_chat.return_value = mock_instance

        llm = create_llm(model="claude-3-5-sonnet-20241022", temperature=0.5)

        mock_chat.assert_called_once()
        assert llm == mock_instance

def test_create_llm_with_custom_params(monkeypatch):
    """测试使用自定义参数创建 LLM"""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    with patch('src.core.llm_setup.ChatAnthropic') as mock_chat:
        mock_instance = Mock()
        mock_chat.return_value = mock_instance

        llm = create_llm(
            model="custom-model",
            temperature=0.9,
            max_tokens=4000
        )

        call_kwargs = mock_chat.call_args[1]
        assert call_kwargs['model'] == "custom-model"
        assert call_kwargs['temperature'] == 0.9
        assert call_kwargs['max_tokens'] == 4000

def test_create_crewai_llm(monkeypatch):
    """测试创建 CrewAI 兼容的 LLM"""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    with patch('src.core.llm_setup.ChatAnthropic') as mock_chat:
        mock_instance = Mock()
        mock_chat.return_value = mock_instance

        llm = create_crewai_llm()

        # 验证返回的是 LangChain 的 ChatAnthropic
        assert llm == mock_instance
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_llm_setup.py -v
```

Expected: `ModuleNotFoundError: No module named 'src.core.llm_setup'`

**Step 3: Write minimal implementation**

Create `src/core/llm_setup.py`:

```python
"""
LLM 设置模块

负责创建和配置 LangChain 与 Anthropic 的 LLM 实例。
"""
from langchain_anthropic import ChatAnthropic
from src.core.config import get_config


def create_llm(
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None
) -> ChatAnthropic:
    """
    创建 LangChain ChatAnthropic 实例

    Args:
        model: 模型名称，如果为 None 则从配置读取
        temperature: 温度参数，如果为 None 则从配置读取
        max_tokens: 最大 token 数，如果为 None 则从配置读取

    Returns:
        ChatAnthropic 实例
    """
    config = get_config()

    return ChatAnthropic(
        model=model or config.model,
        temperature=temperature if temperature is not None else config.temperature,
        max_tokens=max_tokens if max_tokens is not None else config.max_tokens,
        api_key=config.api_key,
    )


def create_crewai_llm() -> ChatAnthropic:
    """
    创建用于 CrewAI 的 LLM 实例

    CrewAI 可以直接使用 LangChain 的 ChatAnthropic。

    Returns:
        ChatAnthropic 实例
    """
    return create_llm()
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/unit/test_llm_setup.py -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/core/llm_setup.py tests/unit/test_llm_setup.py
git commit -m "feat: add LLM setup module with LangChain Anthropic integration"
```

---

## Tools Implementation

### Task 5: Implement FileWriter Tool

**Files:**
- Create: `src/tools/file_writer.py`
- Test: `tests/unit/test_file_writer.py`

**Step 1: Write the failing test**

Create `tests/unit/test_file_writer.py`:

```python
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
    monkeypatch.setenv("CODE_EXECUTION_WORK_DIR", str(tmp_path))

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
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_file_writer.py -v
```

Expected: `ModuleNotFoundError`

**Step 3: Write minimal implementation**

Create `src/tools/file_writer.py`:

```python
"""
文件写入工具

用于将代码写入文件系统。
"""
from pathlib import Path
from src.core.config import get_config


def write_file(file_path: str, content: str) -> dict:
    """
    将内容写入文件

    Args:
        file_path: 文件路径（可以是相对路径）
        content: 文件内容

    Returns:
        包含操作结果的字典
    """
    config = get_config()

    # 如果是相对路径，使用工作目录
    path = Path(file_path)
    if not path.is_absolute():
        path = Path(config.work_dir) / path

    # 确保目录存在
    path.parent.mkdir(parents=True, exist_ok=True)

    # 写入文件
    path.write_text(content, encoding='utf-8')

    return {
        "success": True,
        "file_path": str(path),
        "size": len(content)
    }


class FileWriterTool:
    """CrewAI 兼容的文件写入工具"""

    def __init__(self):
        self.name = "write_file"
        self.description = "将代码或文本内容写入文件。输入: file_path (文件路径), content (文件内容)"

    def get_schema(self) -> dict:
        """返回工具的 schema 定义"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "要写入的文件路径"
                        },
                        "content": {
                            "type": "string",
                            "description": "要写入的内容"
                        }
                    },
                    "required": ["file_path", "content"]
                }
            }
        }

    def run(self, file_path: str, content: str) -> str:
        """
        执行文件写入

        Args:
            file_path: 文件路径
            content: 文件内容

        Returns:
            操作结果描述
        """
        result = write_file(file_path, content)
        return f"文件已写入: {result['file_path']} ({result['size']} 字节)"
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/unit/test_file_writer.py -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/tools/file_writer.py tests/unit/test_file_writer.py
git commit -m "feat: add FileWriter tool"
```

---

### Task 6: Implement CodeExecutor Tool

**Files:**
- Create: `src/tools/code_executor.py`
- Test: `tests/unit/test_code_executor.py`

**Step 1: Write the failing test**

Create `tests/unit/test_code_executor.py`:

```python
import pytest
from src.tools.code_executor import execute_code, CodeExecutorTool

def test_execute_code_success():
    """测试成功执行代码"""
    code = """
def add(a, b):
    return a + b

print(add(2, 3))
"""

    result = execute_code(code)

    assert result["success"] is True
    assert result["returncode"] == 0
    assert "5" in result["stdout"]
    assert result["stderr"] == ""

def test_execute_code_syntax_error():
    """测试代码语法错误"""
    code = "def broken(\n    # 缺少参数和括号"

    result = execute_code(code)

    assert result["success"] is False
    assert result["returncode"] != 0
    assert "SyntaxError" in result["stderr"]

def test_execute_code_runtime_error():
    """测试运行时错误"""
    code = "1 / 0"

    result = execute_code(code)

    assert result["success"] is False
    assert "ZeroDivisionError" in result["stderr"]

def test_execute_code_timeout():
    """测试超时处理"""
    code = "import time; time.sleep(100)"

    result = execute_code(code, timeout=1)

    assert result["success"] is False
    assert "timeout" in result["error"].lower()

def test_CodeExecutorTool_schema():
    """测试 CodeExecutorTool 的 schema"""
    tool = CodeExecutorTool()
    schema = tool.get_schema()

    assert "code" in schema["properties"]
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_code_executor.py -v
```

Expected: `ModuleNotFoundError`

**Step 3: Write minimal implementation**

Create `src/tools/code_executor.py`:

```python
"""
代码执行工具

在沙箱环境中安全执行 Python 代码。
"""
import subprocess
import tempfile
from pathlib import Path
from typing import Optional


def execute_code(code: str, timeout: int = 30) -> dict:
    """
    在临时目录中执行 Python 代码

    Args:
        code: 要执行的 Python 代码
        timeout: 超时时间（秒）

    Returns:
        包含执行结果的字典
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # 写入代码到临时文件
        code_file = Path(tmpdir) / "code.py"
        code_file.write_text(code, encoding='utf-8')

        try:
            # 执行代码
            result = subprocess.run(
                ["python", str(code_file)],
                capture_output=True,
                timeout=timeout,
                cwd=tmpdir,
                text=True
            )

            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "error": None
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": "",
                "error": f"Execution timeout after {timeout} seconds"
            }
        except Exception as e:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": "",
                "error": str(e)
            }


class CodeExecutorTool:
    """CrewAI 兼容的代码执行工具"""

    def __init__(self):
        self.name = "execute_code"
        self.description = "执行 Python 代码并返回输出。输入: code (Python代码字符串), timeout (可选超时秒数，默认30)"

    def get_schema(self) -> dict:
        """返回工具的 schema 定义"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "要执行的 Python 代码"
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "超时时间（秒）",
                            "default": 30
                        }
                    },
                    "required": ["code"]
                }
            }
        }

    def run(self, code: str, timeout: int = 30) -> str:
        """
        执行代码

        Args:
            code: Python 代码
            timeout: 超时时间

        Returns:
            执行结果描述
        """
        result = execute_code(code, timeout)

        if result["success"]:
            output = result["stdout"] or "代码执行成功（无输出）"
            return f"✓ 代码执行成功\n\n输出:\n{output}"
        else:
            error_msg = result["error"] or result["stderr"]
            return f"✗ 代码执行失败\n\n错误:\n{error_msg}"
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/unit/test_code_executor.py -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/tools/code_executor.py tests/unit/test_code_executor.py
git commit -m "feat: add CodeExecutor tool with sandbox execution"
```

---

## Agents Implementation

### Task 7: Implement Coder Agent

**Files:**
- Create: `src/agents/coder.py`
- Test: `tests/unit/test_coder.py`

**Step 1: Write the failing test**

Create `tests/unit/test_coder.py`:

```python
import pytest
from unittest.mock import Mock, patch
from src.agents.coder import create_coder_agent

def test_create_coder_agent_has_correct_attributes(monkeypatch):
    """测试 Coder Agent 有正确的属性"""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    with patch('src.agents.coder.create_llm'):
        mock_llm = Mock()
        with patch('src.agents.coder.Agent') as mock_agent_class:
            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent

            agent = create_coder_agent()

            assert agent == mock_agent
            call_kwargs = mock_agent_class.call_args[1]
            assert call_kwargs['role'] == '高级软件工程师'
            assert 'Python' in call_kwargs['goal']
            assert 'verbose' in call_kwargs
            assert 'allow_delegation' in call_kwargs

def test_coder_has_write_file_tool(monkeypatch):
    """测试 Coder 有 write_file 工具"""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    with patch('src.agents.coder.create_llm'):
        with patch('src.agents.coder.Agent') as mock_agent_class:
            agent = create_coder_agent()
            call_kwargs = mock_agent_class.call_args[1]

            # 验证工具被传递
            assert 'tools' in call_kwargs
            assert len(call_kwargs['tools']) > 0
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_coder.py -v
```

Expected: `ModuleNotFoundError`

**Step 3: Write minimal implementation**

Create `src/agents/coder.py`:

```python
"""
Coder Agent 实现

负责编写高质量的 Python 代码。
"""
from crewai import Agent
from src.core.llm_setup import create_llm
from src.tools.file_writer import FileWriterTool


CODER_SYSTEM_MESSAGE = """你是一位经验丰富的 Python 高级软件工程师。

## 你的职责
1. 根据用户需求编写高质量的 Python 代码
2. 遵循 Python 最佳实践和 PEP 8 规范
3. 添加适当的类型注解和文档字符串
4. 确保代码可读性和可维护性

## 编码标准
- 使用类型注解 (Type Hints)
- 函数和类需要有文档字符串
- 遵循 PEP 8 命名规范
- 添加必要的错误处理
- 编写清晰的注释

## 工作流程
1. 理解任务需求
2. 设计解决方案
3. 编写代码
4. 使用 write_file 工具保存代码到文件
5. 简要说明实现思路

## 输出格式
使用 write_file 工具将代码写入文件，文件名应具有描述性。
"""


def create_coder_agent() -> Agent:
    """
    创建 Coder Agent

    Returns:
        Coder Agent 实例
    """
    llm = create_llm()

    # 创建工具实例
    file_writer = FileWriterTool()

    return Agent(
        role='高级软件工程师',
        goal='编写高质量、符合最佳实践的 Python 代码',
        backstory=CODER_SYSTEM_MESSAGE,
        verbose=True,
        allow_delegation=False,
        llm=llm,
        tools=[file_writer]
    )
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/unit/test_coder.py -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/agents/coder.py tests/unit/test_coder.py
git commit -m "feat: add Coder agent with FileWriter tool"
```

---

### Task 8: Implement Reviewer Agent

**Files:**
- Create: `src/agents/reviewer.py`
- Test: `tests/unit/test_reviewer.py`

**Step 1: Write the failing test**

Create `tests/unit/test_reviewer.py`:

```python
import pytest
from unittest.mock import Mock, patch
from src.agents.reviewer import create_reviewer_agent

def test_create_reviewer_agent_has_correct_attributes(monkeypatch):
    """测试 Reviewer Agent 有正确的属性"""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    with patch('src.agents.reviewer.create_llm'):
        with patch('src.agents.reviewer.Agent') as mock_agent_class:
            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent

            agent = create_reviewer_agent()

            call_kwargs = mock_agent_class.call_args[1]
            assert call_kwargs['role'] == '代码审查专家'
            assert '审查' in call_kwargs['goal']
            assert call_kwargs['allow_delegation'] is False
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_reviewer.py -v
```

Expected: `ModuleNotFoundError`

**Step 3: Write minimal implementation**

Create `src/agents/reviewer.py`:

```python
"""
Reviewer Agent 实现

负责审查代码质量，提供改进建议。
"""
from crewai import Agent
from src.core.llm_setup import create_llm


REVIEWER_SYSTEM_MESSAGE = """你是一位资深的代码审查专家。

## 你的职责
1. 审查 Coder 产生的代码质量
2. 检查代码是否符合 Python 最佳实践
3. 识别潜在的 bug 和安全问题
4. 提供具体的改进建议

## 审查清单
- **正确性**: 代码逻辑是否正确，是否满足需求
- **代码风格**: 是否符合 PEP 8 规范
- **文档**: 是否有清晰的文档字符串和注释
- **性能**: 是否有明显的性能问题
- **安全性**: 是否存在安全漏洞
- **错误处理**: 是否有适当的异常处理

## 输出格式
请提供结构化的审查报告：

1. **总体评价**: 代码质量评分（1-5分）
2. **优点**: 列出代码做得好的地方
3. **问题**: 列出发现的具体问题
4. **建议**: 提供具体的改进建议

如果代码有严重问题，请明确指出需要修改的部分。
"""


def create_reviewer_agent() -> Agent:
    """
    创建 Reviewer Agent

    Returns:
        Reviewer Agent 实例
    """
    llm = create_llm()

    return Agent(
        role='代码审查专家',
        goal='确保代码质量符合高标准，提供专业的改进建议',
        backstory=REVIEWER_SYSTEM_MESSAGE,
        verbose=True,
        allow_delegation=False,
        llm=llm
    )
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/unit/test_reviewer.py -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/agents/reviewer.py tests/unit/test_reviewer.py
git commit -m "feat: add Reviewer agent for code quality checks"
```

---

### Task 9: Implement Tester Agent

**Files:**
- Create: `src/agents/tester.py`
- Test: `tests/unit/test_tester.py`

**Step 1: Write the failing test**

Create `tests/unit/test_tester.py`:

```python
import pytest
from unittest.mock import Mock, patch
from src.agents.tester import create_tester_agent

def test_create_tester_agent_has_correct_attributes(monkeypatch):
    """测试 Tester Agent 有正确的属性"""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    with patch('src.agents.tester.create_llm'):
        with patch('src.agents.tester.Agent') as mock_agent_class:
            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent

            agent = create_tester_agent()

            call_kwargs = mock_agent_class.call_args[1]
            assert call_kwargs['role'] == '测试工程师'
            assert '测试' in call_kwargs['goal']
            assert 'tools' in call_kwargs
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_tester.py -v
```

Expected: `ModuleNotFoundError`

**Step 3: Write minimal implementation**

Create `src/agents/tester.py`:

```python
"""
Tester Agent 实现

负责编写和执行测试用例，验证代码功能。
"""
from crewai import Agent
from src.core.llm_setup import create_llm
from src.tools.code_executor import CodeExecutorTool
from src.tools.file_writer import FileWriterTool


TESTER_SYSTEM_MESSAGE = """你是一位专业的测试工程师。

## 你的职责
1. 为代码编写全面的测试用例
2. 使用 pytest 框架编写测试
3. 执行测试并分析结果
4. 验证代码功能的正确性

## 测试策略
- **正常情况**: 测试预期的正常输入
- **边界情况**: 测试边界值和极端情况
- **错误情况**: 测试异常处理

## 测试结构
使用 Arrange-Act-Assert 模式：
```python
def test_feature():
    # Arrange: 设置测试数据
    input_data = ...

    # Act: 执行被测试的函数
    result = function_under_test(input_data)

    # Assert: 验证结果
    assert result == expected
```

## 工作流程
1. 分析代码需要测试的功能点
2. 编写测试代码
3. 使用 write_file 工具保存测试文件
4. 使用 execute_code 工具运行测试
5. 报告测试结果

## 输出格式
请提供测试报告：
1. **测试覆盖**: 列出测试的功能点
2. **测试代码**: 完整的测试代码
3. **执行结果**: 测试通过/失败情况
4. **问题报告**: 如果有失败的测试，说明原因
"""


def create_tester_agent() -> Agent:
    """
    创建 Tester Agent

    Returns:
        Tester Agent 实例
    """
    llm = create_llm()

    # 创建工具实例
    code_executor = CodeExecutorTool()
    file_writer = FileWriterTool()

    return Agent(
        role='测试工程师',
        goal='编写全面的测试用例，确保代码功能正确',
        backstory=TESTER_SYSTEM_MESSAGE,
        verbose=True,
        allow_delegation=False,
        llm=llm,
        tools=[code_executor, file_writer]
    )
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/unit/test_tester.py -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/agents/tester.py tests/unit/test_tester.py
git commit -m "feat: add Tester agent with CodeExecutor and FileWriter tools"
```

---

### Task 10: Implement Coordinator Agent

**Files:**
- Create: `src/agents/coordinator.py`
- Test: `tests/unit/test_coordinator.py`

**Step 1: Write the failing test**

Create `tests/unit/test_coordinator.py`:

```python
import pytest
from unittest.mock import Mock, patch
from src.agents.coordinator import create_coordinator_agent

def test_create_coordinator_agent_has_correct_attributes(monkeypatch):
    """测试 Coordinator Agent 有正确的属性"""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    with patch('src.agents.coordinator.create_llm'):
        with patch('src.agents.coordinator.Agent') as mock_agent_class:
            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent

            agent = create_coordinator_agent()

            call_kwargs = mock_agent_class.call_args[1]
            assert call_kwargs['role'] == '项目经理'
            assert '协调' in call_kwargs['goal']
            assert call_kwargs['allow_delegation'] is True  # Coordinator 可以委托
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_coordinator.py -v
```

Expected: `ModuleNotFoundError`

**Step 3: Write minimal implementation**

Create `src/agents/coordinator.py`:

```python
"""
Coordinator Agent 实现

负责协调任务流程，汇总最终结果。
"""
from crewai import Agent
from src.core.llm_setup import create_llm


COORDINATOR_SYSTEM_MESSAGE = """你是项目团队的协调者和项目经理。

## 你的职责
1. 理解用户的需求和任务目标
2. 协调团队成员（Coder、Reviewer、Tester）完成工作
3. 汇总各阶段的工作成果
4. 生成最终的交付报告

## 工作流程
你将看到：
1. Coder 产生的代码
2. Reviewer 的审查报告
3. Tester 的测试结果

## 输出格式
请生成一个完整的交付报告：

```markdown
# 任务交付报告

## 任务描述
[原始任务描述]

## 交付内容
- 代码文件: [文件路径]
- 测试文件: [测试文件路径]

## 代码审查总结
- 评分: [1-5分]
- 主要优点: [列出优点]
- 改进建议: [列出建议]

## 测试结果
- 测试通过率: [百分比]
- 测试覆盖: [描述覆盖情况]

## 使用说明
[如何使用交付的代码]

## 注意事项
[任何需要注意的事项]
```

确保报告清晰、完整、易于理解。
"""


def create_coordinator_agent() -> Agent:
    """
    创建 Coordinator Agent

    Returns:
        Coordinator Agent 实例
    """
    llm = create_llm()

    return Agent(
        role='项目经理',
        goal='协调团队工作，确保高质量交付',
        backstory=COORDINATOR_SYSTEM_MESSAGE,
        verbose=True,
        allow_delegation=True,  # Coordinator 可以委托任务给其他 Agent
        llm=llm
    )
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/unit/test_coordinator.py -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/agents/coordinator.py tests/unit/test_coordinator.py
git commit -m "feat: add Coordinator agent for task orchestration"
```

---

## Tasks Implementation

### Task 11: Implement Coding Task

**Files:**
- Create: `src/tasks/coding_task.py`
- Test: `tests/unit/test_coding_task.py`

**Step 1: Write the failing test**

Create `tests/unit/test_coding_task.py`:

```python
import pytest
from unittest.mock import Mock
from src.tasks.coding_task import create_coding_task
from src.agents.coder import create_coder_agent

def test_create_coding_task_has_correct_attributes():
    """测试 coding_task 有正确的属性"""
    mock_coder = Mock()
    mock_coder.role = "高级软件工程师"

    task = create_coding_task(mock_coder)

    assert task.agent == mock_coder
    assert "编写" in task.description.lower()
    assert "expected_output" in task.__dict__

def test_coding_task_with_custom_description():
    """测试自定义任务描述"""
    mock_coder = Mock()

    task = create_coding_task(
        agent=mock_coder,
        description="实现二分查找算法"
    )

    assert "二分查找" in task.description
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_coding_task.py -v
```

Expected: `ModuleNotFoundError`

**Step 3: Write minimal implementation**

Create `src/tasks/coding_task.py`:

```python
"""
Coding Task 实现

定义代码编写任务。
"""
from crewai import Task


def create_coding_task(agent, description: str | None = None) -> Task:
    """
    创建代码编写任务

    Args:
        agent: 执行任务的 Agent (Coder)
        description: 任务描述，如果为 None 则使用默认

    Returns:
        Task 实例
    """
    if description is None:
        description = """根据用户需求编写 Python 代码。

请使用 write_file 工具将代码保存到文件。
代码应该：
1. 符合 Python 最佳实践
2. 包含类型注解
3. 有清晰的文档字符串
4. 有适当的错误处理
"""

    return Task(
        description=description,
        agent=agent,
        expected_output="编写完成的 Python 代码文件，并使用 write_file 工具保存"
    )
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/unit/test_coding_task.py -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/tasks/coding_task.py tests/unit/test_coding_task.py
git commit -m "feat: add coding task definition"
```

---

### Task 12: Implement Review Task

**Files:**
- Create: `src/tasks/review_task.py`
- Test: `tests/unit/test_review_task.py`

**Step 1: Write the failing test**

Create `tests/unit/test_review_task.py`:

```python
import pytest
from unittest.mock import Mock
from src.tasks.review_task import create_review_task

def test_create_review_task_has_correct_attributes():
    """测试 review_task 有正确的属性"""
    mock_reviewer = Mock()

    task = create_review_task(mock_reviewer)

    assert task.agent == mock_reviewer
    assert "审查" in task.description.lower()

def test_review_task_context():
    """测试审查任务依赖上下文"""
    mock_reviewer = Mock()

    task = create_review_task(mock_reviewer)

    # 验证任务需要上下文
    assert hasattr(task, 'context')
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_review_task.py -v
```

Expected: `ModuleNotFoundError`

**Step 3: Write minimal implementation**

Create `src/tasks/review_task.py`:

```python
"""
Review Task 实现

定义代码审查任务。
"""
from crewai import Task


def create_review_task(agent, context: list | None = None) -> Task:
    """
    创建代码审查任务

    Args:
        agent: 执行任务的 Agent (Reviewer)
        context: 依赖的上下文任务（通常是 coding_task）

    Returns:
        Task 实例
    """
    description = """审查 Coder 产生的代码质量。

请检查：
1. 代码是否正确实现了需求
2. 是否符合 Python 最佳实践
3. 是否有清晰的结构和文档
4. 是否有潜在的问题或改进空间

提供结构化的审查报告，包括评分、优点、问题和建议。
"""

    return Task(
        description=description,
        agent=agent,
        context=context or [],
        expected_output="代码审查报告，包含评分、优缺点分析和改进建议"
    )
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/unit/test_review_task.py -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/tasks/review_task.py tests/unit/test_review_task.py
git commit -m "feat: add review task definition with context support"
```

---

### Task 13: Implement Testing Task

**Files:**
- Create: `src/tasks/testing_task.py`
- Test: `tests/unit/test_testing_task.py`

**Step 1: Write the failing test**

Create `tests/unit/test_testing_task.py`:

```python
import pytest
from unittest.mock import Mock
from src.tasks.testing_task import create_testing_task

def test_create_testing_task_has_correct_attributes():
    """测试 testing_task 有正确的属性"""
    mock_tester = Mock()

    task = create_testing_task(mock_tester)

    assert task.agent == mock_tester
    assert "测试" in task.description.lower()

def test_testing_task_context():
    """测试测试任务依赖上下文"""
    mock_tester = Mock()

    task = create_testing_task(mock_tester)

    assert hasattr(task, 'context')
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_testing_task.py -v
```

Expected: `ModuleNotFoundError`

**Step 3: Write minimal implementation**

Create `src/tasks/testing_task.py`:

```python
"""
Testing Task 实现

定义测试任务。
"""
from crewai import Task


def create_testing_task(agent, context: list | None = None) -> Task:
    """
    创建测试任务

    Args:
        agent: 执行任务的 Agent (Tester)
        context: 依赖的上下文任务（通常是 coding_task 和 review_task）

    Returns:
        Task 实例
    """
    description = """为代码编写并执行测试用例。

请：
1. 分析代码需要测试的功能点
2. 编写 pytest 测试代码
3. 使用 write_file 保存测试文件
4. 使用 execute_code 运行测试
5. 报告测试结果

测试应包括：
- 正常情况测试
- 边界情况测试
- 错误处理测试
"""

    return Task(
        description=description,
        agent=agent,
        context=context or [],
        expected_output="测试文件和测试执行结果报告"
    )
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/unit/test_testing_task.py -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/tasks/testing_task.py tests/unit/test_testing_task.py
git commit -m "feat: add testing task definition"
```

---

### Task 14: Implement Final Task

**Files:**
- Create: `src/tasks/final_task.py`
- Test: `tests/unit/test_final_task.py`

**Step 1: Write the failing test**

Create `tests/unit/test_final_task.py`:

```python
import pytest
from unittest.mock import Mock
from src.tasks.final_task import create_final_task

def test_create_final_task_has_correct_attributes():
    """测试 final_task 有正确的属性"""
    mock_coordinator = Mock()

    task = create_final_task(mock_coordinator)

    assert task.agent == mock_coordinator
    assert "汇总" in task.description or "交付" in task.description

def test_final_task_context():
    """测试最终任务依赖所有前置任务"""
    mock_coordinator = Mock()

    task = create_final_task(mock_coordinator)

    assert hasattr(task, 'context')
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_final_task.py -v
```

Expected: `ModuleNotFoundError`

**Step 3: Write minimal implementation**

Create `src/tasks/final_task.py`:

```python
"""
Final Task 实现

定义最终汇总任务。
"""
from crewai import Task


def create_final_task(agent, context: list | None = None) -> Task:
    """
    创建最终汇总任务

    Args:
        agent: 执行任务的 Agent (Coordinator)
        context: 依赖的上下文任务（所有前置任务）

    Returns:
        Task 实例
    """
    description = """汇总所有阶段的工作成果，生成最终交付报告。

请整理：
1. Coder 产生的代码和文件
2. Reviewer 的审查意见
3. Tester 的测试结果

生成一个完整、清晰的交付报告，包含：
- 任务概述
- 交付内容清单
- 代码质量评估
- 测试结果总结
- 使用说明
- 注意事项
"""

    return Task(
        description=description,
        agent=agent,
        context=context or [],
        expected_output="完整的任务交付报告"
    )
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/unit/test_final_task.py -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/tasks/final_task.py tests/unit/test_final_task.py
git commit -m "feat: add final summary task definition"
```

---

## Crew Assembly

### Task 15: Implement CodeDevelopmentCrew

**Files:**
- Create: `src/crews/code_crew.py`
- Test: `tests/unit/test_code_crew.py`

**Step 1: Write the failing test**

Create `tests/unit/test_code_crew.py`:

```python
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.crews.code_crew import CodeDevelopmentCrew

def test_code_crew_initialization(monkeypatch):
    """测试 CodeDevelopmentCrew 初始化"""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    with patch('src.crews.code_crew.Crew') as mock_crew_class:
        mock_crew = MagicMock()
        mock_crew_class.return_value = mock_crew

        crew = CodeDevelopmentCrew()

        assert crew.crew == mock_crew
        # 验证 Crew 被正确创建
        mock_crew_class.assert_called_once()

def test_code_crew_kickoff(monkeypatch):
    """测试 crew.kickoff 调用"""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    with patch('src.crews.code_crew.Crew') as mock_crew_class:
        mock_crew = MagicMock()
        mock_result = MagicMock()
        mock_result.raw = "任务完成"
        mock_crew.kickoff.return_value = mock_result
        mock_crew_class.return_value = mock_crew

        crew = CodeDevelopmentCrew()
        result = crew.kickoff("实现快速排序")

        mock_crew.kickoff.assert_called_once()
        assert result == mock_result

def test_code_crew_has_four_agents(monkeypatch):
    """测试 Crew 有 4 个 Agent"""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    with patch('src.crews.code_crew.Crew') as mock_crew_class:
        with patch('src.crews.code_crew.create_coordinator_agent'):
            with patch('src.crews.code_crew.create_coder_agent'):
                with patch('src.crews.code_crew.create_reviewer_agent'):
                    with patch('src.crews.code_crew.create_tester_agent'):
                        mock_crew = MagicMock()
                        mock_crew_class.return_value = mock_crew

                        crew = CodeDevelopmentCrew()

                        # 验证 agents 列表长度
                        call_kwargs = mock_crew_class.call_args[1]
                        assert 'agents' in call_kwargs
                        assert len(call_kwargs['agents']) == 4
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_code_crew.py -v
```

Expected: `ModuleNotFoundError`

**Step 3: Write minimal implementation**

Create `src/crews/code_crew.py`:

```python
"""
CodeDevelopmentCrew 实现

组装代码开发团队的 Crew。
"""
from crewai import Crew, Process
from src.agents.coordinator import create_coordinator_agent
from src.agents.coder import create_coder_agent
from src.agents.reviewer import create_reviewer_agent
from src.agents.tester import create_tester_agent
from src.tasks.coding_task import create_coding_task
from src.tasks.review_task import create_review_task
from src.tasks.testing_task import create_testing_task
from src.tasks.final_task import create_final_task


class CodeDevelopmentCrew:
    """代码开发团队 Crew"""

    def __init__(self):
        """初始化 Crew"""
        # 创建 Agents
        self.coordinator = create_coordinator_agent()
        self.coder = create_coder_agent()
        self.reviewer = create_reviewer_agent()
        self.tester = create_tester_agent()

        # 创建 Tasks
        self.coding_task = create_coding_task(self.coder)
        self.review_task = create_review_task(self.reviewer, context=[self.coding_task])
        self.testing_task = create_testing_task(self.tester, context=[self.coding_task, self.review_task])
        self.final_task = create_final_task(self.coordinator, context=[self.coding_task, self.review_task, self.testing_task])

        # 创建 Crew
        self.crew = Crew(
            agents=[self.coordinator, self.coder, self.reviewer, self.tester],
            tasks=[self.coding_task, self.review_task, self.testing_task, self.final_task],
            process=Process.sequential,
            verbose=True
        )

    def kickoff(self, task_description: str):
        """
        启动 Crew 执行任务

        Args:
            task_description: 任务描述

        Returns:
            Crew 执行结果
        """
        # 更新 coding_task 的描述
        self.coding_task.description = f"""任务: {task_description}

请根据上述任务需求编写 Python 代码。
使用 write_file 工具将代码保存到文件。
"""

        return self.crew.kickoff()
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/unit/test_code_crew.py -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/crews/code_crew.py tests/unit/test_code_crew.py
git commit -m "feat: add CodeDevelopmentCrew with sequential process"
```

---

## CLI Implementation

### Task 16: Implement CLI Interface

**Files:**
- Create: `app/cli.py`
- Create: `app/__main__.py`

**Step 1: Create CLI implementation**

Create `app/cli.py`:

```python
"""
命令行界面

使用 Typer 实现的 CLI 工具。
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import typer
from rich.console import Console
from rich.panel import Panel
from src.crews.code_crew import CodeDevelopmentCrew
from src.utils.logger import setup_logging, get_logger

app = typer.Typer(help="Project 4 CrewAI - 多 Agent 代码开发团队")
console = Console()


@app.command()
def run(
    task: str = typer.Option(..., "--task", "-t", help="任务描述"),
    debug: bool = typer.Option(False, "--debug", "-d", help="调试模式")
):
    """
    执行代码开发任务

    Example:
        python -m app.cli --task "实现快速排序算法"
        python -m app.cli -t "创建一个 Todo 类" --debug
    """
    # 设置日志
    log_level = "DEBUG" if debug else "INFO"
    setup_logging(log_level)
    logger = get_logger(__name__)

    # 显示欢迎信息
    console.print(Panel.fit(
        "[bold blue]Project 4 CrewAI[/bold blue]\n"
        "[dim]多 Agent 代码开发团队[/dim]",
        border_style="blue"
    ))

    console.print(f"\n[bold]任务:[/bold] {task}\n")

    try:
        # 创建 Crew
        logger.info("初始化 CodeDevelopmentCrew...")
        crew = CodeDevelopmentCrew()

        # 执行任务
        logger.info("开始执行任务...")
        with console.status("[bold green]Agents 工作中...", spinner="dots"):
            result = crew.kickoff(task)

        # 显示结果
        console.print("\n[bold green]✓ 任务完成[/bold green]\n")

        if hasattr(result, 'raw'):
            console.print(Panel(result.raw, title="执行结果", border_style="green"))
        else:
            console.print(str(result))

    except Exception as e:
        console.print(f"\n[bold red]✗ 执行失败:[/bold red] {e}\n")
        if debug:
            import traceback
            console.print(traceback.format_exc())
        raise typer.Exit(1)


@app.command()
def version():
    """显示版本信息"""
    console.print("[bold blue]Project 4 CrewAI[/bold blue] version 0.1.0")


if __name__ == "__main__":
    app()
```

Create `app/__main__.py`:

```python
"""
允许使用 python -m app 运行
"""
from app.cli import app

if __name__ == "__main__":
    app()
```

**Step 2: Test CLI help**

```bash
cd /root/Learn/llm-learning/project4-crewai
python -m app.cli --help
```

Expected: Help message displayed

**Step 3: Commit**

```bash
git add app/cli.py app/__main__.py
git commit -m "feat: add CLI interface with Typer"
```

---

## Web UI Implementation

### Task 17: Implement Web UI with Streamlit

**Files:**
- Create: `app/web.py`

**Step 1: Create Web UI implementation**

Create `app/web.py`:

```python
"""
Streamlit Web 界面
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from src.crews.code_crew import CodeDevelopmentCrew
from src.utils.logger import setup_logging

# 页面配置
st.set_page_config(
    page_title="Project 4 CrewAI",
    page_icon="🤖",
    layout="wide"
)

# 初始化日志
setup_logging()


def main():
    """主界面"""
    st.title("🤖 Project 4 CrewAI")
    st.markdown("---")

    # 侧边栏配置
    with st.sidebar:
        st.header("⚙️ 配置")

        st.markdown("### Agent 团队")
        st.markdown("""
        - **Coordinator** - 项目经理
        - **Coder** - 高级工程师
        - **Reviewer** - 代码审查专家
        - **Tester** - 测试工程师
        """)

        st.markdown("---")
        st.markdown("### 关于")
        st.markdown("""
        基于 CrewAI 框架的多 Agent
        代码开发团队系统。
        """)

    # 主界面
    col1, col2 = st.columns([3, 1])

    with col1:
        st.header("📝 任务输入")

        task = st.text_area(
            "描述你的代码需求",
            placeholder="例如：实现一个快速排序算法...",
            height=100
        )

        col_a, col_b = st.columns(2)
        with col_a:
            debug_mode = st.checkbox("调试模式", value=False)
        with col_b:
            execute = st.button("🚀 执行任务", type="primary", use_container_width=True)

    with col2:
        st.header("📊 状态")
        if 'result' in st.session_state:
            if st.session_state.get('success'):
                st.success("✓ 任务完成")
            else:
                st.error("✗ 执行失败")

    # 执行任务
    if execute and task:
        st.markdown("---")

        # 显示进度
        with st.spinner("🔄 Agents 工作中..."):
            try:
                # 创建 Crew
                crew = CodeDevelopmentCrew()

                # 执行任务
                result = crew.kickoff(task)

                # 保存结果
                st.session_state.result = str(result)
                st.session_state.success = True

            except Exception as e:
                st.session_state.result = f"错误: {str(e)}"
                st.session_state.success = False

        st.rerun()

    # 显示结果
    if 'result' in st.session_state:
        st.markdown("---")
        st.header("📄 执行结果")

        if st.session_state.success:
            st.success(st.session_state.result)
        else:
            st.error(st.session_state.result)


if __name__ == "__main__":
    main()
```

**Step 2: Test Web UI**

```bash
# 检查语法
python -c "import app.web; print('OK')"
```

Expected: No syntax errors

**Step 3: Commit**

```bash
git add app/web.py
git commit -m "feat: add Streamlit web interface"
```

---

## Integration Testing

### Task 18: Add Integration Tests

**Files:**
- Create: `tests/integration/test_end_to_end.py`
- Create: `tests/fixtures/sample_tasks.yaml`

**Step 1: Create sample tasks fixture**

Create `tests/fixtures/sample_tasks.yaml`:

```yaml
simple_algorithm:
  description: "实现一个计算斐波那契数列的函数"
  expected_files:
    - fib.py

data_processing:
  description: "创建一个处理 CSV 数据的脚本，计算平均值"
  expected_files:
    - data_processor.py
```

**Step 2: Create integration test**

Create `tests/integration/test_end_to_end.py`:

```python
"""
端到端集成测试

这些测试需要真实的 API key，标记为 integration。
"""
import pytest
import os
from src.crews.code_crew import CodeDevelopmentCrew


@pytest.mark.integration
def test_simple_algorithm_end_to_end():
    """测试简单算法的端到端流程"""
    # 跳过如果没有 API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip("需要 ANTHROPIC_API_KEY")

    crew = CodeDevelopmentCrew()
    result = crew.kickoff("实现一个计算两数之和的函数")

    assert result is not None
    # 验证结果包含预期的输出
    result_str = str(result).lower()
    assert any(keyword in result_str for keyword in ["函数", "function", "def", "code"])


@pytest.mark.integration
def test_crew_has_all_agents():
    """测试 Crew 包含所有 Agent"""
    if not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip("需要 ANTHROPIC_API_KEY")

    crew = CodeDevelopmentCrew()

    # 验证所有 Agent 都被创建
    assert crew.coordinator is not None
    assert crew.coder is not None
    assert crew.reviewer is not None
    assert crew.tester is not None

    # 验证所有 Task 都被创建
    assert crew.coding_task is not None
    assert crew.review_task is not None
    assert crew.testing_task is not None
    assert crew.final_task is not None


@pytest.mark.integration
def test_task_dependencies():
    """测试任务依赖关系"""
    if not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip("需要 ANTHROPIC_API_KEY")

    crew = CodeDevelopmentCrew()

    # review_task 应该依赖 coding_task
    assert crew.coding_task in crew.review_task.context

    # testing_task 应该依赖 coding_task 和 review_task
    assert crew.coding_task in crew.testing_task.context
    assert crew.review_task in crew.testing_task.context

    # final_task 应该依赖所有前置任务
    assert crew.coding_task in crew.final_task.context
    assert crew.review_task in crew.final_task.context
    assert crew.testing_task in crew.final_task.context
```

**Step 3: Update pytest configuration**

Create `pytest.ini`:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    integration: 需要真实 API key 的集成测试
    unit: 单元测试（不需要 API key）
addopts =
    -v
    --tb=short
```

**Step 4: Run unit tests only**

```bash
pytest tests/unit/ -v -m "not integration"
```

Expected: All unit tests PASS

**Step 5: Commit**

```bash
git add tests/integration/test_end_to_end.py tests/fixtures/sample_tasks.yaml pytest.ini
git commit -m "test: add integration tests with markers"
```

---

## Documentation

### Task 19: Update README and Documentation

**Files:**
- Modify: `README.md`
- Create: `docs/USAGE.md`

**Step 1: Update main README**

Update `README.md`:

```markdown
# Project 4: Multi-Agent Code Development Team (CrewAI Version)

> 使用 CrewAI 框架实现的多 Agent 协作系统

[![CrewAI](https://img.shields.io/badge/CrewAI-0.80.0-blue)](https://www.crewai.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-green)](https://www.python.org/)

## 项目简介

这是 Project 4 的 CrewAI 实现版本，与 [AutoGen 版本](../project4-multiagent/) 进行对比学习。

## Agent 角色

| Agent | 角色定位 | 主要职责 |
|-------|---------|---------|
| **Coordinator** | 项目经理 | 协调任务流程，分配任务，汇总结果 |
| **Coder** | 高级工程师 | 编写高质量 Python 代码 |
| **Reviewer** | 代码审查专家 | 检查代码质量，提出改进建议 |
| **Tester** | 测试工程师 | 编写和执行测试用例 |

## 快速开始

### 安装

\`\`\`bash
# 克隆项目
cd /root/Learn/llm-learning/project4-crewai

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，添加 ANTHROPIC_API_KEY
\`\`\`

### 使用方式

#### 命令行界面

\`\`\`bash
# 基础用法
python -m app.cli --task "实现快速排序算法"

# 调试模式
python -m app.cli -t "实现二分查找" --debug

# 查看帮助
python -m app.cli --help
\`\`\`

#### Web 界面

\`\`\`bash
# 启动 Streamlit
streamlit run app/web.py

# 然后在浏览器中打开 http://localhost:8501
\`\`\`

## 技术栈

- **CrewAI 0.80.0** - 多 Agent 编排框架
- **LangChain** - LLM 集成层
- **Anthropic Claude** - LLM 提供商
- **Streamlit** - Web 界面
- **Typer** - CLI 框架

## 项目结构

\`\`\`
project4-crewai/
├── src/
│   ├── agents/          # Agent 定义
│   ├── crews/           # Crew 组装
│   ├── tasks/           # Task 定义
│   ├── tools/           # 工具函数
│   ├── core/            # 核心配置
│   └── utils/           # 工具函数
├── app/
│   ├── cli.py           # 命令行界面
│   └── web.py           # Streamlit Web 界面
├── tests/               # 测试
├── outputs/             # 生成的代码
└── docs/                # 文档
\`\`\`

## 测试

\`\`\`bash
# 运行所有单元测试（不需要 API key）
pytest tests/unit/ -v

# 运行集成测试（需要 API key）
pytest tests/integration/ -v -m integration

# 运行测试并查看覆盖率
pytest tests/ --cov=src --cov-report=term-missing
\`\`\`

## 与 AutoGen 版本的对比

| 特性 | AutoGen | CrewAI |
|------|---------|--------|
| 对话机制 | `initiate_chat()` / `run()` | `crew.kickoff()` |
| Agent 交互 | 对话历史 | Tasks + Tools |
| 流程控制 | 内置对话循环 | Sequential/Hierarchical Process |
| LLM 集成 | 直接配置 | 通过 LangChain |

## 许可证

MIT
```

**Step 2: Create usage documentation**

Create `docs/USAGE.md`:

```markdown
# 使用指南

## CLI 用法

### 基础示例

\`\`\`bash
# 实现算法
python -m app.cli --task "实现带类型注解的快速排序算法"

# 创建类
python -m app.cli -t "创建一个 Stack 类，包含 push、pop、peek 方法"

# 数据处理
python -m app.cli -t "写一个函数读取 CSV 文件并计算平均值"
\`\`\`

### 调试模式

\`\`\`bash
python -m app.cli -t "你的任务" --debug
\`\`\`

## Web UI 用法

1. 启动服务：`streamlit run app/web.py`
2. 打开浏览器访问 http://localhost:8501
3. 在文本框输入任务描述
4. 点击"执行任务"按钮
5. 等待 Agents 完成工作
6. 查看执行结果

## 输出文件

生成的代码保存在 `outputs/` 目录。

## 环境变量

在 `.env` 文件中配置：

\`\`\`bash
ANTHROPIC_API_KEY=sk-ant-xxx
ANTHROPIC_MODEL=claude-sonnet-4-20250514
TEMPERATURE=0.7
CODE_EXECUTION_WORK_DIR=./outputs
LOG_LEVEL=INFO
\`\`\`
```

**Step 3: Commit**

```bash
git add README.md docs/USAGE.md
git commit -m "docs: update README and add usage guide"
```

---

## Final Steps

### Task 20: Final Verification and Cleanup

**Step 1: Run all tests**

```bash
# 运行所有单元测试
pytest tests/unit/ -v -m "not integration"

# 运行所有测试（如果有 API key）
pytest tests/ -v
```

**Step 2: Check code quality**

```bash
# 检查导入
python -c "import src.crews.code_crew; import app.cli; import app.web; print('All imports OK')"
```

**Step 3: Final commit**

```bash
git add .
git commit -m "chore: final cleanup and verification"
```

---

## Implementation Complete

After all tasks are completed, the project should have:

- ✅ 完整的项目结构
- ✅ 配置管理模块
- ✅ 4 个 Agent (Coordinator, Coder, Reviewer, Tester)
- ✅ 4 个 Task (coding, review, testing, final)
- ✅ 2 个 Tool (FileWriter, CodeExecutor)
- ✅ CodeDevelopmentCrew 组装
- ✅ CLI 界面 (Typer)
- ✅ Web 界面 (Streamlit)
- ✅ 单元测试
- ✅ 集成测试
- ✅ 完整文档
